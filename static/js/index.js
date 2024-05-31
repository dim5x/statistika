$(document).ready(function () {
    // Register the datetime sorting plugin with DataTables
    $.fn.dataTable.moment('DD.MM.YYYY');

    // Initialize DataTable
    var table = $('.data').DataTable();

    // Make cells editable
    $('.data tbody td').editable(function (value, settings) {
        var cell = table.cell(this);
        var aPos = cell.index();

        $.ajax({
            type: "POST",
            url: "/update",
            data: {
                row_id: aPos.row,
                column_id: aPos.column,
                // column_name: table.column(aPos.column).header().innerText,
                value: value
            },
            success: function (response) {
                if (response.success) {
                    cell.data(value).draw();
                } else {
                    alert("Update failed: " + response.error);
                }
            },
            error: function () {
                alert("An error occurred while updating the cell.");
            }
        });

        return value;
    }, {
        "height": "14px"
    });
});
