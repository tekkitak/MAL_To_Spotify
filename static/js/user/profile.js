$().ready(function () {
    $('body').on('click', '#edit-profile-btn', function () {
        $('.user-form').removeAttr('disabled');
        $('#default-buttons').hide();
        $('#edit-buttons').show();
    });

    $('body').on('click', '#cancel-edit-profile-btn', function () {
        $('.user-form').attr('disabled', 'disabled');
        $('#default-buttons').show();
        $('#edit-buttons').hide();
    });


});