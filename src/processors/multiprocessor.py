# -*- coding: utf-8 -*-

# Copyright (c) 2020 shmilee

'''
Contains multiprocess processor class.
'''

import multiprocessing

from .processor import Processor, plog
from ..glogger import get_glogger_work_initializer
from ..loaders import get_pckloader
from ..utils import inherit_docstring, MP_RWLock


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

    # # Start Convert Part

    def _convert_worker(self, core, lock, name_it=True):
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
            lock.release()

    def convert(self, add_desc=None):
        '''
        Use multiprocessing to convert raw data.
        '''
        if self.multiproc > 1:
            self._pre_convert(add_desc=add_desc)
            nworkers = min(self.multiproc, len(self.converters))
            plog.debug('%d processes to work!' % nworkers)
            with get_glogger_work_initializer() as loginitializer:
                lock = self.manager.RLock()
                with multiprocessing.Pool(
                        processes=nworkers,
                        initializer=loginitializer) as pool:
                    results = [pool.apply_async(
                        self._convert_worker, (core, lock))
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
        plog.debug("Changing %s data cache store to '%s'." % (ext2, D))
        self.ressaver.set_store(D)
        self.resloader = get_pckloader(D)

    @staticmethod
    def _filter_couple_figlabel(_couple):
        '''Return figlabel, kwargs'''
        if isinstance(_couple, str):
            return _couple, {}
        elif isinstance(_couple, dict):
            figlabel = _couple.pop('figlabel', None)
            if figlabel:
                return figlabel, _couple
            else:
                return None, "No figlabel in couple_figlabel"
        else:
            return None, "Invalid couple_figlabel type"

    def _dig_worker(self, couple_figlabel, redig, post, callback,
                    rwlock, name_it=True):
        '''
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
            return None, kwargs, None, update
        if name_it:
            multiprocessing.current_process().name = figlabel
        try:
            rwlock.reader_lock.acquire()
            data = self._before_new_dig(figlabel, redig, kwargs)
        finally:
            rwlock.reader_lock.release()
        if data[0] is None:
            return (*data, update)
        digcore, gotfiglabel, results = data
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
        if post:
            results = digcore.post_dig(results)
        if callable(callback):
            callback(results)
        return accfiglabel, results, digcore.post_template, update

    def multi_dig(self, *couple_figlabels, redig=False, post=True,
                  callback=None):
        '''
        Get digged results of *couple_figlabels*.
        Multiprocess version of :meth:`dig`.
        Return a list of :meth:`dig` return.

        Parameters
        ----------
        couple_figlabels: list of couple_figlabel
            couple_figlabel can be figlabel str or dict, like
            {'figlabel': 'group/fignum', 'other kwargs': True}
        others: see :meth:`dig`

        Notes
        -----
        Using a read write lock to avoid error about unpickle pckloader and
        saving pcksaver together. So most codes like *post*, *callback* are
        multiprocessing, except saving results:
        1. *post*, `post_dig` is expected to complete immediately.
        2. *callback*, it is user-defined, maybe not multiprocess safe.
        3. Saving dig-results, because savers may be not multiprocess safe.
        '''
        if len(couple_figlabels) == 0:
            plog.warning("please pass at least one figlabel!")
            return []
        multi_results = []
        if self.multiproc > 1:
            nworkers = min(self.multiproc, len(couple_figlabels))
            with get_glogger_work_initializer() as loginitializer:
                rwlock = MP_RWLock(self.manager)
                with multiprocessing.Pool(
                        processes=nworkers,
                        initializer=loginitializer) as pool:
                    async_results = [pool.apply_async(
                        self._dig_worker,
                        (couple_figlabel, redig, post, callback, rwlock))
                        for couple_figlabel in couple_figlabels]
                    pool.close()
                    pool.join()
                update = 0
                for res in async_results:
                    data = res.get()
                    multi_results.append(data[:3])
                    update = max(data[3], update)
            if update == 1:
                self._after_save_new_dig(update_file=False)
            elif update == 2:
                self._after_save_new_dig(update_file=True)
        else:
            plog.warning("Max number of worker processes is one, "
                         "use for loop to multi_dig!")
            for _couple in couple_figlabels:
                figlabel, kwargs = self._filter_couple_figlabel(_couple)
            if figlabel is None:
                multi_results.append((None, kwargs, None))
            else:
                multi_results.append(self.dig(
                    figlabel, redig=redig, post=post, callback=callback,
                    **kwargs))
        return multi_results

    # # End Dig Part

    # # Start Export Part

    # # End Export Part

    # # Start Visplt Part

    # # End Visplt Part
