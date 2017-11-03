/**
 * make_radio_button_choice_extension() makes one input field as an extension of the last option of
 * a radio button group. To be specific, this function creates the effect that when the last option
 * of a radio button group is chosen, an input field will appear, allows users to provide more
 * information. The following diagram provides an example to capture the concept. Let's assume we
 * want to have a radio group to get user's favorite fruit. If the fruit is not on the list, we
 * want the user to enter the customized fruit:
 *
 *     O  Apple
 *     O  Banana
 *     @  Others, my favorite fruit is [______].
 *
 * Now we will provide the preparation steps before you use this function. When you declare
 * Django's Form class (including ModelForm), we need to have at least two fields, and let's
 * call these field names defined in the form object called 'menu' and 'extra'. The field
 * 'menu' uses RadioSelect widget, and 'extra' uses any widget which creates a regular input tag.
 * The idea is to move the input tag and append to the end of the radio group. By default,
 * Django will generate the html with the following:
 *
 *     <div class='form-group'>
 *       <label ... />
 *       <div id='id_menu'>
 *         <div class='radio'> ... option 1 ... </div>
 *         <div class='radio'> ... option 2 ... </div>
 *         <div class='radio'> ... option 3 ... </div>
 *       </div>
 *     </div>
 *     <div class='form-group'>
 *       <label ... />
 *       <input id='id_extra' />
 *     </div>
 *
 * To achieve the desired effect, we add an extension div right after div of the last option, which
 * includes:
 *
 *     <div id='id_menu_extension'>
 *       extension prefix
 *       <input id='id_extra'>
 *       extension postfix
 *     </div>
 *
 * and then remove the second div with class 'form-group' (the one which surrounded the input tag.)
 *
 * Note we assume all the names and id attributes of all the html tags follow Django's naming
 * conventions without modification. For example, every id should start with 'id_'.
 *
 *
 * Parameters:
 *   radio_button_group_id: The id attribute of the div which embraces all the radio buttons.
 *   input_id: The id attribute of the input tag, which is supposed to be moved inside the radio
 *       group.
 *   append_format: Defines when the last option is checked, what is supposed to be displayed. It
 *       accepts a string which contains '<input>', which will be placed with the input tag
 *       specified above. Take the above example, append_format will be set as
 *       "extension prefix <input> extension postfix".
 *   input_width: The width of the input tag.
 */
function make_radio_button_choice_extension(radio_button_group_id, input_id,
    append_format=": <input>", input_width=50) {

  input_object = $("#" + input_id);
  obselete_form_group = $(input_object).parent();
  
  $(input_object).width(input_width);
  $(input_object).css('display', 'inline-block');

  // segment append_format into `block_prefix` + <input> + `block_postfix`
  tidx = append_format.indexOf("<input>");
  if (tidx === -1) {
    block_prefix = ": ";
    block_postfix = "";
  }
  else {
    block_prefix = append_format.substring(0, tidx);
    block_postfix = append_format.substring(tidx + 7);
  }

  // create and place the extension div
  extension_block_id = radio_button_group_id + "_extension";
  radio_button_group_div = $("#" + radio_button_group_id);
  $(radio_button_group_div).children().last().css('display', 'inline-block');

  last_radio_button_block = $('div', radio_button_group_div).last();
  last_radio_button_id = $('input', last_radio_button_block).attr('id')

  $(radio_button_group_div).append(
      '<div id="' + extension_block_id + '" style="display:inline-block">'
      + block_prefix + '</div>');
  extension_block_div = $("#" + extension_block_id);
  $(input_object).appendTo(extension_block_div);
  $(extension_block_div).append(block_postfix);

  // remove the empty div
  $(obselete_form_group).remove();

  // assign callback for capturing the change of radio buttons 
  on_change_callback = function() {
    if ($("#" + last_radio_button_id + ":checked").is(":checked"))
      $(extension_block_div).css('visibility', 'visible');
    else
      $(extension_block_div).css('visibility', 'hidden');
  }

  on_change_callback();

  radio_button_group_name = radio_button_group_id.substring(3);  // remove 'id_' in the front
  $('input[type=radio][name=' + radio_button_group_name + ']').change(on_change_callback);
}
