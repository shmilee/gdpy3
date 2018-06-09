<script>
// 返回顶部
$('.scroll-head').click(function() {
    $('html,body').animate({
        scrollTop: '0px'
    },
    600);
});
// 隐藏代码
//code_show=true;
$('.scroll-hidecode').click(function() {
    //if (code_show){
    //    $('div.input').hide(600);
    //    $('.scroll-hidecode i').addClass('fa-eye-slash');
    //    $(this).attr('title', '{{ scroll_showcode_title }}');
    //} else {
    //    $('div.input').show(600);
    //    $('.scroll-hidecode i').removeClass('fa-eye-slash');
    //    $(this).attr('title', '{{ scroll_hidecode_title }}');
    //};
    //code_show = !code_show;
    $('div.input').toggle(600);
    $('.scroll-hidecode i').toggleClass('fa-eye-slash');
    $(this).attr('title',
        $('.scroll-hidecode i').hasClass('fa-eye-slash')?'{{ scroll_showcode_title }}':'{{ scroll_hidecode_title }}'
    );
});
//回到底部
$('.scroll-bottom').click(function() {
    $('html,body').animate({
        scrollTop: $(document).height() - $(window).height()
    },
    600);
});
</script>
