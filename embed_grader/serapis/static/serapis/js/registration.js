function check_password() {
    var pass1 = $('#id_password1');
    var pass2 = $('#id_password2');
    var msg = $('#password2-message');

    const error_color = 'red';
    const good_color = 'white';
    
    if (pass1.val() === pass2.val()) {
        msg.text('');
        pass2.css('background-color', good_color);
    } else {
        msg.text('Passwords do not match.');
        pass2.css('background-color', error_color);
    }
}

$(document).ready(function (){
    $('#id_password2').keyup(check_password);
});