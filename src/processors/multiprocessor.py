# -*- coding: utf-8 -*-

# Copyright (c) 2020-2021 shmilee

'''
Contains multiprocess processor class.
'''

import os
import multiprocessing

from .processor import Processor, plog
from ._mp_rwlock import MP_RWLock
from ..glogger import LogWorkInitializer
from ..loaders import get_pckloader
from ..utils import inherit_docstring


__all__ = ['MultiProcessor']


def _copydoc_func(docs):
    name, doc = docs[0]
    assert name == 'Processor'
    return (doc[doc.find('Attributes'):],), {}


@inherit_docstring((Processor,), _copydoc_func, template=None)
class MultiProcessor(Processor):
    '''
    Multiprocess Processor class.

    {0}3. :attr:`multiproc` is the max number of worker processes,
       default multiprocessing.cpu_count().
    '''

    parallel = 'multiprocess'
    multiproc = multiprocessing.cpu_count()
    manager = multiprocessing.Manager()

    @property
    def name(self):
        return type(self).__name__[5:]

    def _count_task_done(self, lock, count, total, desc):
        '''
        Parameters
        ----------
        lock: multiprocessing lock
        count: multiprocessing value number of completed tasks
        total: total number of tasks
        desc: description of task
        '''
        with lock:
            count.value += 1
            done = count.value
        plog.info("Task: %s (%d/%d) done." % (desc, done, total))

    # # Start Convert Part

    def _convert_worker(self, core, lock, count, total, name_it=True):
        '''
        Parameters
        ----------
        core: Converter core instance
        lock: multiprocessing lock
        name_it: bool
            When using multiprocessing,
            *name_it* is True, processname is set to :attr:`core.groupnote`.
        '''
        if name_it:
            multiprocessing.current_process().name = core.groupnote
        data = core.convert()
        lock.acquire()
        try:
            plog.info("Writing data in group %s ..." % core.group)
            with self.pcksaver:
                self.pcksaver.write(core.group, data)
        finally:
            self._count_task_done(lock, count, total, 'Convert')
            lock.release()

    def convert(self, add_desc=None):
        '''
        Use multiprocessing to convert raw data.
        '''
        if self.multiproc > 1:
            self._pre_convert(add_desc=add_desc)
            nworkers = min(self.multiproc, len(self.converters))
            plog.debug('%d processes to work!' % nworkers)
            with LogWorkInitializer() as loginitializer:
                lock = self.manager.RLock()
                count = self.manager.Value('i', 0, lock=False)
                total = len(self.converters)
                with multiprocessing.Pool(
                        processes=nworkers,
                        initializer=loginitializer) as pool:
                    results = [pool.apply_async(
                        self._convert_worker, (core, lock, count, total))
                        for core in self.converters]
                    pool.close()
                    pool.join()
            self._post_convert()
        else:
            plog.warning("Max number of worker processes is one, "
                         "use for loop to convert data!")
            super(MultiProcessor, self).convert(add_desc=add_desc)

    multi_convert = convert

    # # End Convert Part

    # # Start Dig Part

    def set_prefer_ressaver(self, ext2='digged', oldext2='converted',
                            overwrite=False):
        super(MultiProcessor, self).set_prefer_ressaver(
            ext2=ext2, oldext2=oldext2, overwrite=overwrite)
        D = self.manager.dict()
        plog.debug("Changing %s data cache store to '%r'." % (ext2, D))
        self.ressaver.set_store(D)
        self.resloader = get_pckloader(D)

    @staticmethod
    def _filter_couple_figlabel(_couple):
        '''Return figlabel, kwargs'''
        if isinstance(_couple, str):
            return _couple, {}
        elif isinstance(_couple, dict):
            copy = _couple.copy()
            figlabel = copy.pop('figlabel', None)
            if figlabel:
                return figlabel, copy
            else:
                return None, "No figlabel in couple_figlabel"
        else:
            return None, "Invalid couple_figlabel type"

    def _dig_worker_with_rwlock(self, couple_figlabel, redig, callback, post,
                                rwlock, lock, count, total, name_it=True):
        '''
        Find old dig results, dig new if needed, then save them.

        Parameters
        ----------
        couple_figlabel: figlabel str or dict contains figlabel
        rwlock: read-write lock
        name_it: bool
            When using multiprocessing,
            *name_it* is True, processname is set to *figlabel*.
        '''
        update = 0
        figlabel, kwargs = self._filter_couple_figlabel(couple_figlabel)
        if figlabel is None:
            self._count_task_done(lock, count, total, 'Dig')
            return None, kwargs, None, update
        if name_it:
            multiprocessing.current_process().name = figlabel
        try:
            rwlock.reader_lock.acquire()
            # after reopen resfileloader, then try to find old results
            self.resfileloader = get_pckloader(self.resfilesaver.get_store())
            data = self._before_new_dig(figlabel, redig, kwargs)
        finally:
            rwlock.reader_lock.release()
        digcore, gotfiglabel, results = data
        if digcore is None:
            self._count_task_done(lock, count, total, 'Dig')
            return (*data, update)
        if results is None:
            accfiglabel, results, digtime = self._do_new_dig(digcore, kwargs)
            try:
                rwlock.writer_lock.acquire()
                # ressaver, having multiprocessing DictProxy's own lock
                # but we use rwlock instead of it.
                self._cachesave_new_dig(accfiglabel, gotfiglabel, results)
                update = 1
                if self.resfilesaver and digtime > self.dig_acceptable_time:
                    # long execution time
                    self._filesave_new_dig(
                        accfiglabel, gotfiglabel, results, digcore)
                    update = 2
            finally:
                rwlock.writer_lock.release()
        else:
            accfiglabel = gotfiglabel
        self._count_task_done(lock, count, total, 'Dig')
        if callable(callback):
            callback(accfiglabel, results)
        if post:
            results = digcore.post_dig(results)
        return (accfiglabel, results, digcore.post_template,
                update, figlabel, digcore.kwoptions)

    def _dig_worker_with_lock(self, digcore, kwargs, gotfiglabel, callback,
                              post, lock, count, total, name_it=True):
        '''
        Dig new results, and save them.

        Parameters
        ----------
        lock: multiprocessing lock
        name_it: bool
            When using multiprocessing,
            *name_it* is True, processname is set to *figlabel*.
        '''
        if name_it:
            multiprocessing.current_process().name = digcore.figlabel
        accfiglabel, results, digtime = self._do_new_dig(digcore, kwargs)
        try:
            lock.acquire()
            self._cachesave_new_dig(accfiglabel, gotfiglabel, results)
            if self.resfilesaver and digtime > self.dig_acceptable_time:
                # long execution time
                self._filesave_new_dig(
                    accfiglabel, gotfiglabel, results, digcore)
        finally:
            self._count_task_done(lock, count, total, 'Dig')
            lock.release()
        if callable(callback):
            callback(accfiglabel, results)
        if post:
            results = digcore.post_dig(results)
        return (accfiglabel, results, digcore.post_template,
                digcore.kwoptions)

    def multi_dig(self, *couple_figlabels, whichlock='write',
                  redig=False, callback=None, post=True):
        '''
        Get digged results of *couple_figlabels*.
        Multiprocess version of :meth:`dig`.
        Return a list of :meth:`dig` return.

        Parameters
        ----------
        couple_figlabels: list of couple_figlabel
            couple_figlabel can be figlabel str or dict, like
            {'figlabel': 'group/fignum', 'other kwargs': True}
        whichlock: str, 'write' or 'read-write'
            default 'write', means only using a write lock
        others: see :meth:`dig`

        Notes
        -----
        1. When using a write lock, only new_dig figlabel and its *callback*,
           *post* will be multiprocessing, others like digged figlabel
           and their *callback*, *post* are not!
            1). *callback*, it is user-defined, maybe not multiprocess safe.
                Recommand using :attr:`manager` to create a list or dict for
                *callback* to store data.
            2). *post*, `post_dig` is expected to complete immediately.
            3). Saving dig-results, savers may be not multiprocess safe.
        2. If using a read write lock to avoid error about unpickle pckloader
           and saving pcksaver together, most codes like *callback*, *post*
           are multiprocessing, except saving results.
        3. Useing a write lock or read write lock depends on how many digged
           figlabels, their results size and where they saved.
        '''
        if len(couple_figlabels) == 0:
            plog.warning("please pass at least one figlabel!")
            return []
        multi_results = []
        if self.multiproc > 1:
            if whichlock not in ('write', 'read-write'):
                plog.warning("Set default write lock, not %s!" % whichlock)
                whichlock = 'write'
            if whichlock == 'write':
                couple_todo = []
                for idx, _couple in enumerate(couple_figlabels):
                    figlabel, kwargs = self._filter_couple_figlabel(_couple)
                    if figlabel is None:
                        multi_results.append((None, kwargs, None))
                    else:
                        data = self._before_new_dig(figlabel, redig, kwargs)
                        digcore, gotfiglabel, results = data
                        if digcore is None:
                            multi_results.append(data)
                        else:
                            if results is None:
                                # tag new_dig figlabels
                                multi_results.append(idx)
                                couple_todo.append(
                                    (idx, digcore, kwargs, gotfiglabel))
                            else:
                                # find saved dig results
                                accfiglabel = gotfiglabel
                                if callable(callback):
                                    callback(accfiglabel, results)
                                if post:
                                    results = digcore.post_dig(results)
                                multi_results.append((accfiglabel, results,
                                                      digcore.post_template))
                # do new_dig figlabels
                if len(couple_todo) > 0:
                    nworkers = min(self.multiproc, len(couple_todo))
                    with LogWorkInitializer() as loginitializer:
                        plog.debug("Using a write lock!")
                        lock = self.manager.RLock()
                        count = self.manager.Value('i', 0, lock=False)
                        total = len(couple_todo)
                        # While resfilesaver is saving to the path,
                        # fork will fail to reopen resfileloader.path.
                        # Fortunately, resfileloader is useless in workers.
                        self.resfileloader = None
                        with multiprocessing.Pool(
                                processes=nworkers,
                                initializer=loginitializer) as pool:
                            async_results = [(idx, core, pool.apply_async(
                                self._dig_worker_with_lock,
                                (core, kws, gotfgl, callback, post, lock,
                                    count, total)))
                                for idx, core, kws, gotfgl in couple_todo]
                            pool.close()
                            pool.join()
                        for idx, core, res in async_results:
                            data = res.get()
                            assert multi_results[idx] == idx
                            multi_results[idx] = data[:3]
                            if core.kwoptions is None:
                                core.kwoptions = data[3]
                        self.resloader = get_pckloader(
                            self.ressaver.get_store())
                        self.resfileloader = get_pckloader(
                            self.resfilesaver.get_store())
            else:
                # with 'read-write' lock
                nworkers = min(self.multiproc, len(couple_figlabels))
                with LogWorkInitializer() as loginitializer:
                    plog.debug("Using a read-write lock!")
                    rwlock = MP_RWLock(self.manager)
                    lock = self.manager.RLock()  # for count
                    count = self.manager.Value('i', 0, lock=False)
                    total = len(couple_figlabels)
                    # resfileloader reopen in workers, not forking
                    self.resfileloader = None
                    with multiprocessing.Pool(
                            processes=nworkers,
                            initializer=loginitializer) as pool:
                        async_results = [pool.apply_async(
                            self._dig_worker_with_rwlock,
                            (couple_figlabel, redig, callback, post, rwlock,
                                lock, count, total))
                            for couple_figlabel in couple_figlabels]
                        pool.close()
                        pool.join()
                    update = 0
                    for res in async_results:
                        data = res.get()
                        multi_results.append(data[:3])
                        update = max(data[3], update)
                        if data[3] > 0:
                            core = self._availablelabels_lib[data[4]]
                            if core.kwoptions is None:
                                core.kwoptions = data[5]
                # reset resfileloader in mainprocess
                self.resfileloader = get_pckloader(
                    self.resfilesaver.get_store())
                if update > 0:
                    self.resloader = get_pckloader(self.ressaver.get_store())
        else:
            plog.warning("Max number of worker processes is one, "
                         "use for loop to multi_dig!")
            for _couple in couple_figlabels:
                figlabel, kwargs = self._filter_couple_figlabel(_couple)
                if figlabel is None:
                    multi_results.append((None, kwargs, None))
                else:
                    multi_results.append(self.dig(
                        figlabel, redig=redig, callback=callback, post=post,
                        **kwargs))
        return multi_results

    # # End Dig Part

    # # Start Export Part

    def multi_export(self, *couple_figlabels, what='axes', fmt='dict',
                     whichlock='write', callback=None):
        '''
        Get and assemble digged results, template of *couple_figlabels*.
        Multiprocess version of :meth:`export`.
        Return a list of :meth:`export` return in format *fmt*.

        Parameters
        ----------
        couple_figlabels: list of couple_figlabel
            couple_figlabel can be figlabel str or dict, like
            {'figlabel': 'group/fignum', 'other kwargs': True}
        whichlock: see :meth:`multi_dig`
        callback: see :meth:`multi_dig`, only for what='axes'
        others: see :meth:`export`
        '''
        if what not in ('axes', 'options'):
            what = 'axes'
        if fmt not in ('dict', 'pickle', 'json'):
            fmt = 'dict'
        multi_results, couple_todo = [], []
        for idx, _couple in enumerate(couple_figlabels):
            figlabel, kwargs = self._filter_couple_figlabel(_couple)
            if figlabel in self.availablelabels:
                if what == 'axes':
                    # todo
                    multi_results.append(idx)
                    couple_todo.append((idx, figlabel, kwargs, _couple))
                elif what == 'options':
                    digcore = self._availablelabels_lib[figlabel]
                    exportcore = self._get_exporter(digcore.post_template)
                    if exportcore:
                        if digcore.kwoptions is None:
                            # todo
                            multi_results.append(idx)
                            couple_todo.append(
                                (idx, figlabel, kwargs, _couple))
                        else:
                            resopt = exportcore.export_options(
                                digcore.kwoptions, otherinfo=dict(
                                    status=200, figlabel=figlabel))
                            # add
                            multi_results.append(resopt)
                    else:
                        status, reason = 500, 'invalid template'
                        # add
                        multi_results.append(dict(
                            status=status, reason=reason, figlabel=figlabel))

            else:
                plog.error("%s: Figure %s not found!" % (self.name, figlabel))
                status, reason = 404, 'figlabel not found'
                # add
                multi_results.append(
                    dict(status=status, reason=reason, figlabel=figlabel))
        if len(couple_todo) > 0:
            _couple_dig = [_c[3] for _c in couple_todo]
            if what == 'axes':
                multi_dig_res = self.multi_dig(
                    *_couple_dig, whichlock=whichlock,
                    callback=callback, post=True)
                for jdx, (label_kw, res, tmpl) in enumerate(multi_dig_res):
                    idx, figlabel, kwargs = couple_todo[jdx][:3]
                    exportcore = self._get_exporter(tmpl)
                    if exportcore:
                        # add
                        assert multi_results[idx] == idx
                        multi_results[idx] = exportcore.export(
                            res, otherinfo=dict(status=200,
                                                figlabel=figlabel,
                                                accfiglabel=label_kw,
                                                ), **kwargs)
                    else:
                        status, reason = 500, 'invalid template'
                        if label_kw is None or tmpl is None:
                            reason = res
                        # add
                        multi_results.append(dict(
                            status=status, reason=reason, figlabel=figlabel))
            elif what == 'options':
                multi_dig_res = self.multi_dig(
                    *_couple_dig, post=False, whichlock=whichlock)
                for idx, figlabel, kwargs, _couple in couple_todo:
                    digcore = self._availablelabels_lib[figlabel]
                    exportcore = self._get_exporter(digcore.post_template)
                    # add
                    assert multi_results[idx] == idx
                    multi_results[idx] = exportcore.export_options(
                        digcore.kwoptions, otherinfo=dict(
                            status=200, figlabel=figlabel))
        # format multi_results
        exportcore = self._get_exporter('tmpl_line')
        return exportcore.fmt_export(multi_results, fmt=fmt)

    # # End Export Part

    # # Start Visplt Part

    def _visplt_worker(self, results, revis, savename, saveext, savepath,
                       mpl_backend, lock, count, total, name_it=True):
        '''
        Use results create figure, then save it.

        Parameters
        ----------
        name_it: bool
            When using multiprocessing,
            *name_it* is True, processname is set to figlabel.
        '''
        figlabel = results['figlabel']
        if name_it:
            multiprocessing.current_process().name = figlabel
        if results['status'] == 200:
            accfiglabel = results['accfiglabel']
            try:
                self.visplter.subprocess_fix_backend_etc(
                    mpl_backend=mpl_backend)
                plog.debug("Start creating %s ..." % accfiglabel)
                figure = self.visplter.create_template_figure(
                    results, replace=revis)
            except Exception:
                plog.error("%s: Failed to create figure %s!" % (
                    self.name, accfiglabel),  exc_info=1)
                self._count_task_done(lock, count, total, 'Visplt')
                return False, accfiglabel, '(500) failed to create'
            else:
                _fl = accfiglabel if savename == 'accfiglabel' else figlabel
                fname = '%s.%s' % (_fl.replace('/', '-'), saveext)
                fpath = os.path.join(savepath, fname)
                try:
                    plog.debug("Saving %s ..." % accfiglabel)
                    self.visplter.save_figure(accfiglabel, fpath)
                except Exception:
                    plog.error("%s: Failed to save figure %s!" % (
                        self.name, accfiglabel),  exc_info=1)
                    self._count_task_done(lock, count, total, 'Visplt')
                    return False, accfiglabel, '(500) failed to save'
                else:
                    self._count_task_done(lock, count, total, 'Visplt')
                    return True, accfiglabel, fname
        else:
            status, reason = results['status'], results['reason']
            plog.error("%s: Failed to create figure %s: (%d) %s" % (
                self.name, figlabel, status, reason),  exc_info=1)
            self._count_task_done(lock, count, total, 'Visplt')
            return False, results['accfiglabel'], "(%d) %s" % (status, reason)

    def multi_visplt(self, *couple_figlabels, revis=False,
                     savename='figlabel', saveext='png', savepath='.',
                     mpl_backend='agg', whichlock='write', callback=None):
        '''
        Get results of *couple_figlabels* and visualize(plot), save them.
        Multiprocess version of :meth:`visplt`.

        Returns
        -------
        two list:
            1. [(accfiglabel, save file), ...]
            2. [(accfiglabel, failed reason), ...]

        Parameters
        ----------
        couple_figlabels: list of couple_figlabel
            couple_figlabel can be figlabel str or dict, like
            {'figlabel': 'group/fignum', 'other kwargs': True}
        savename: str
            'figlabel'(default) or 'accfiglabel'
        saveext: str
            figure type, 'png'(default), 'pdf', 'ps', 'eps', 'svg', 'jpg'
        savepath: str
            the directory to saving figures
        mpl_backend: str, optional
            Set matplotlib backend when :attr:`visplter` type is 'mpl::'.
            Recommand using non_interactive backends, like 'agg', 'cairo' etc.
        whichlock: see :meth:`multi_dig`
        callback: see :meth:`multi_dig`
        others: see :meth:`visplt`
        '''
        if not self.visplter:
            plog.error("%s: Need a visplter object!" % self.name)
            return
        multi_results = self.multi_export(
            *couple_figlabels, what='axes', fmt='dict',
            whichlock=whichlock, callback=callback)
        success, fail = [], []
        if not os.path.isdir(savepath):
            os.mkdir(savepath)
        nworkers = min(self.multiproc, len(multi_results))
        with LogWorkInitializer() as loginitializer:
            lock = self.manager.RLock()
            count = self.manager.Value('i', 0, lock=False)
            total = len(multi_results)
            with multiprocessing.Pool(
                    processes=nworkers,
                    initializer=loginitializer) as pool:
                async_results = [pool.apply_async(
                    self._visplt_worker,
                    (results, revis, savename, saveext, savepath,
                        mpl_backend, lock, count, total))
                    for results in multi_results]
                pool.close()
                pool.join()
            for res in async_results:
                data = res.get()
                if data[0]:
                    success.append(data[1:])
                else:
                    fail.append(data[1:])
        return success, fail

    # # End Visplt Part
