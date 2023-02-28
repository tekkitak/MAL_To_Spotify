$().ready(function() {
    let dataTable = $('#openings_table').dataTable({
        dom: 'lfrtipB',
        ajax: {
            url: "/ajaxTest",
            dataSrc: ""
        },
        stateSave: true,
        columns: [
            {
                title: "Uri",
                data: "op_uri",
            },
            { 
                title: 'Name',
                name:'first',
                data: "title" 
            },
            { 
                title: "Song",
                data: "op_title",
                render: ( data, type, row, meta ) => {
                    return `<a href='https://open.spotify.com/album/${row.op_uri.split(':').slice(-1)}' target='_blank'>${data}</a>`
                }
            },
            {
                title: "Include",
                data: null,
                render: (data, type, row) => {
                    return `<input type='checkbox' name='${row.op_uri}'>`
                }
            }
        ],
        columnDefs: [
            { targets: [0], visible: false},
        ],
        rowsGroup: [
            'first:name'
        ],
        buttons: [
            {
                text: 'Add to playlist',
                action: function ( e, dt, node, config ) {
                    // Get selected rows by checking the checkbox

                    let uris = [];
                    $('#openings_table input[type=checkbox]:checked').each(function() {
                        uris.push($(this).attr('name'));
                    });
                    console.log(uris);

                    $.ajax({
                        url: "/addPlaylist",
                        type: "POST",
                        data: JSON.stringify(uris),
                        contentType: "application/json",
                        success: function (data) {
                            console.log(data);
                        }
                    });
                }
            },
            {
                text: 'Select all shown',
                action: function ( e, dt, node, config ) {
                    $('#openings_table input[type=checkbox]').each(function() {
                        $(this).prop('checked', true);
                    });
                }
            }
        ]
    });
});