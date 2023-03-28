$().ready(function () {
    $('#playlists-select').select2({
        placeholder: 'Select a playlist or create a new one',
        tags: true,
        createTag: function (params) {
            var term = $.trim(params.term);
        
            if (term === '') {
              return null;
            }
            // console.log(term);
            return {
              id: 'new:' + term,
              text: term,
              newTag: true // add additional parameters
            }
          }
    })


    let dataTable = $('#openings_table').dataTable({
        dom: 'lfrtipB',
        ajax: {
            url: "/mal/animeOpList",
            dataSrc: (json) => {
                return json.filter(function (item) {
                    return true
                    return item.op_uri != null;
                });
            }
        },
        stateSave: true,
        paging: false,
        scrollY: "calc(100vh - 500px)",
        scrollCollapse: true,

        columns: [
            {
                title: "Uri",
                data: "op_uri",
            },
            {
                title: 'Name',
                name: 'first',
                data: "title"
            },
            {
                title: "Song",
                data: "op_title",
                render: (data, type, row, meta) => {
                    if(row.op_uri == null)
                    return data;
                    return `<a href='https://open.spotify.com/track/${row.op_uri.split(':').slice(-1)}' target='_blank'>${data}</a>`
                }
            },
            {
                title: "Artist",
                data: "op_artist",
            },
            {
                title: "Include",
                data: null,
                render: (data, type, row) => {
                    if(row.op_uri == null)
                        return `<input type='checkbox' name='${row.op_uri}' disabled='true'>`
                    return `<input type='checkbox' name='${row.op_uri}'>`
                }
            }
        ],
        columnDefs: [
            { targets: [0], visible: false },
        ],
        rowsGroup: [
            'first:name',
        ],
        buttons: [
            {
                text: 'Add to playlist',
                action: function (e, dt, node, config) {
                    let uris = [];
                    $('#openings_table input[type=checkbox]:checked').each(function () {
                        //check if checkbox is not disabled
                        if (!$(this).prop('disabled'))
                            uris.push($(this).attr('name'));
                    });

                    //get playlist id from select2 plugin dropdown
                    let playlist_id = $('#playlists-select').select2('data')[0].id;
                    if (playlist_id.startsWith('new:')) {
                        playlist_name = playlist_id.split(':')[1];
                        $.ajax({
                            url: '/spotify/createPlaylist/' + playlist_name,
                            type: 'GET',
                            success: function (data) {
                                playlist_id = data;
                            },
                            error: function (data) {
                                console.log(data);
                            },
                            async: false
                        });
                    }

                    if (playlist_id == null) {
                        return;
                    }
                    window.location.href = `/spotify/addSongs/${playlist_id}/${uris.join(',')}`;
                }
            },
            {
                text: 'Select all shown',
                action: function (e, dt, node, config) {
                    $('#openings_table input[type=checkbox]').each(function () {
                        if (!$(this).prop('disabled'))
                            $(this).prop('checked', true);
                    });
                }
            },
            {
                text: 'Deselect all shown',
                action: function (e, dt, node, config) {
                    $('#openings_table input[type=checkbox]').each(function () {
                        if (!$(this).prop('disabled'))
                            $(this).prop('checked', false);
                    });
                }
            },
        ]
    });

});