django.jQuery(document).ready(function(){
    $('.add_keyvaluewidget').click(function(e){
        var $this = $(this),
            widget_block =$this.closest('.keyvaluewidget'),
            children = widget_block.children();
        if (children.length){
            var new_row = $(children[0]).clone(true),
                last_row = $(children[children.length - 2]),
                html = new_row.html(),
                index = children.length - 1;

            for (var i = 0; i < 2; i++) {
                var id = $(new_row.find('input')[i]).attr('id') + index.toString();
                $(new_row.find('label')[i]).attr('for', id);
                $(new_row.find('input')[i]).attr('id', id);
                $(new_row.find('input')[i]).attr('name',
                    $(new_row.find('input')[i]).attr('name') + index.toString()
                );
            }
            $(new_row).insertBefore($this.parent()).slideDown();
        }
    });

    $('.keyvaluewidget').delegate('.inline-deletelink', 'click', function(){
        $(this).parent().parent().slideUp(function(){$(this).remove()});
    })
});
