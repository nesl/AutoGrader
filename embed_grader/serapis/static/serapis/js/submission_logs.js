function initialize_submission_log_table() {
  $(document).ready(function() {
    $('#data-table tfoot th').each(function () {
      var title = $(this).text();
      $(this).html('<input type="text" placeholder="Search ' + title + '" />' );
    });

    // sort by descending submission time which is the 3rd column in the table
    var table = $('#data-table').DataTable({"order":[[3, "desc"]]});

    table.columns().every(function() {
      var that = this;

      $('input', this.footer()).on('keyup change', function() {
        if (that.search() !== this.value) {
          that.search( this.value ).draw();
        }
      });
    });
  });
}
