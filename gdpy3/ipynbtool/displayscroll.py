# -*- coding: utf-8 -*-

# Copyright (c) 2017 shmilee

__all__ = ['scrollbar']

try:
    from IPython.display import HTML
except ImportError:
    log.error('If you want to use scrollbar, please install IPython.')
    raise

_head_title = '返回顶部'
_hidecode_title = '隐藏代码'
_showcode_title = '显示代码'
_bottom_title = '回到底部'

_SCROLL_BAR_CSS = r'''
<style type="text/css">
.scroll-bar {
    width:36px;
    float:right;
    position:fixed;
    right:12px;
    bottom:36px;
    z-index:9999;
}
.scroll-bar li {
    list-style: none;
}
.scroll-bar li a {
    background:#fff;
    font-size:18px;
    color:#a1a1a1;
    width:32px;
    height:32px;
    line-height:30px;
    text-align:center;
    vertical-align:middle;
    margin-top:4px;
    display:block;
    cursor:pointer;
    background:rgba(255,255,255,.6);
    border:1px solid #d8d8d8;
    border-radius:5px;
    box-shadow:0 1px 1px rgba(0,0,0,.04);
}
.scroll-bar li a:hover {
    background:#337ab7;
    color:#fff;
    border:1px solid #337ab7;
    transition:all .2s ease-in 0s;
}
%s
</style>
'''

_SCROLL_BAR_DIV = r'''
<div class="scroll-bar">
%s
</div>
'''

_scroll_head_div = r'''
    <li>
        <a class="scroll-head" title="%s">
            <i class="fa fa-angle-up"></i>
        </a>
    </li>
''' % _head_title

_scroll_hidecode_div = r'''
    <li>
        <a class="scroll-hidecode" title="%s">
            <i class="fa fa-eye"></i>
        </a>
    </li>
''' % _hidecode_title

_scroll_bottom_div = r'''
    <li>
        <a class="scroll-bottom" title="%s">
            <i class="fa fa-angle-down"></i>
        </a>
    </li>
''' % _bottom_title

_SCROLL_BAR_SCRIPT = r'''
<script>
%s
</script>
'''

_scroll_head_script = r'''
// 返回顶部
$('.scroll-head').click(function() {
    $('html,body').animate({
        scrollTop: '0px'
    },
    600);
});
'''

_scroll_hidecode_script = r'''
// 隐藏代码
//code_show=true;
$('.scroll-hidecode').click(function() {
    //if (code_show){
    //    $('div.input').hide(600);
    //    $('.scroll-hidecode i').addClass('fa-eye-slash');
    //    $(this).attr('title', '%s');
    //} else {
    //    $('div.input').show(600);
    //    $('.scroll-hidecode i').removeClass('fa-eye-slash');
    //    $(this).attr('title', '%s');
    //};
    //code_show = !code_show;
    $('div.input').toggle(600);
    $('.scroll-hidecode i').toggleClass('fa-eye-slash');
    $(this).attr('title',
        $('.scroll-hidecode i').hasClass('fa-eye-slash')?'%s':'%s'
    );
});
''' % (_showcode_title, _hidecode_title, _showcode_title, _hidecode_title)

_scroll_bottom_script = r'''
//回到底部
$('.scroll-bottom').click(function() {
    $('html,body').animate({
        scrollTop: $(document).height() - $(window).height()
    },
    600);
});
'''


def scrollbar(*args):
    '''
    Return IPython.core.display.HTML object, scrollbar.

    Notes
    -----
    args: default ['head', 'hidecode', 'bottom']
    '''
    elements = {
        'head': [None, _scroll_head_div, _scroll_head_script],
        'hidecode': [None, _scroll_hidecode_div, _scroll_hidecode_script],
        'bottom': [None, _scroll_bottom_div, _scroll_bottom_script],
    }
    if not args:
        args = ['head', 'hidecode', 'bottom']

    elements_css = ''
    elements_div = ''
    elements_script = ''
    for ele in args:
        if ele not in elements:
            print("'%s' not supported!" % ele)
            continue
        if elements[ele][0]:
            elements_css += elements[ele][0]
        if elements[ele][1]:
            elements_div += elements[ele][1]
        if elements[ele][2]:
            elements_script += elements[ele][2]
    barhtml = (
        _SCROLL_BAR_CSS % elements_css
        + _SCROLL_BAR_DIV % elements_div
        + _SCROLL_BAR_SCRIPT % elements_script
    )

    return HTML(barhtml)
