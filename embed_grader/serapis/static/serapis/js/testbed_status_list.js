function render_table() {
  $.ajax({
    url: "/ajax-get-testbeds/",
    type: "GET",
    dataType: 'JSON',
    success: function(testbeds) {
      $("#block-fetching-data-msg").css("display", "none");
      $("#block-no-testbed-msg").css("display", "none");
      $("#block-testbeds").css("display", "none");

      if (testbeds.length == 0) {
        $("#block-no-testbed-msg").css("display", "block");
      }
      else {
        $("#block-testbeds").css("display", "block");

        var tbody = $("#status-table-body");
        tbody.empty();

        for (i = 0; i < testbeds.length; i++) {
          testbed = testbeds[i];
          tbody.append("<tr class='modifiable-rows'>")
          var tr = $('#status-table-body').find('tr:last');
          tr.append("<td>" + testbed.id + "</td>");
          tr.append("<td>" + testbed.ip_address + "</td>");
          tr.append("<td>" + testbed.status + "</td>");
          tr.append("<td>Status: " + testbed.report_status + "<br/>(" + testbed.report_time + ")</td>");

          task = testbed.task;
          if (task === null) {
            tr.append("<td>(No executing task)</td>");
            tr.append("<td>&nbsp;</td>")
          }
          else {
            tr.append("<td>"
                + "Course: " + task.course + "<br/>"
                + "Assignment: " + task.assignment + "<br/>"
                + "Task Name: " + task.task_name + "<br/>"
                + "Submission ID: " + task.submission_id
                + "</td>")
            tr.append("<td><a onclick=abort_task(" + testbed.id + ") class='btn btn-primary'>Abort Task</a></td>")
          }
        }
      }

      $("#block-updated-time").html("Last table updated time: " + (new Date().toLocaleString()));
    },
    failure: function(data) {
      $("#block-updated-time").html("Last data query time: " + (new Date().toLocaleString()) + " <span style='color:red'>(Failed to fetch testbed list)</span>");
    }
  });
}

function abort_task(testbed_id) {
  ajax_setup();
  $.ajax({
    url: "/ajax-abort-testbed-task/",
    type: 'POST',
    dataType: 'JSON',
    data: {id: testbed_id},
    success: function(data) {
    },
    failure: function(data) {
      alert('Got an error dude');
    }
  });
}
