$().ready(function () {
    $('#playlists-select').select2({
        placeholder: 'Select a playlist or create a new one',
        tags: true,
        createTag: function (params) {
            var term = $.trim(params.term);

            if (term === '') {
                return null;
            }

            return {
                id: 'new:' + term,
                text: term,
                newTag: true // add additional parameters
            }
        }
    });

    $('#show-mal-token').on('click', () => {
        $('#mal-token').toggle();
    })

    $('#show-spotify-token').on('click', () => {
        $('#spotify-token').toggle();
    })


    let dataTable = $('#openings_table').dataTable({
        dom: 'lfrtpB',
        ajax: {
            url: "/api/mal/animeOpList",
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
                // TODO: add force update button
                title: 'Name',
                name: 'first',
                data: "title"
            },
            {
                title: "Song",
                data: "op_title",
                render: (data, type, row, meta) => {
                    out = `<div class='popup d-flex flex-row justify-content-between'>`
                    button = `<button class='btn btn-sm btn-primary' onclick='popup-${row.anime_id}'>Change</button>`
                    if (row.op_uri == null)
                        out += data
                    else
                        out += `<a href='https://open.spotify.com/track/${row.op_uri.split(':').slice(-1)}' target='_blank'>${data}</a>`
                    return out + button + `</div>`
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
                    if (row.op_uri == null)
                        return `<input type='checkbox' class='form-check-input border border-danger' name='${row.op_uri}' disabled='true'>`
                    return `<input type='checkbox' class='form-check-input border border-primary' name='${row.op_uri}'>`
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
                            url: '/api/spotify/createPlaylist/' + playlist_name,
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
                    //maximum number of songs that can be added to a playlist in one request is 100 so we need to split the uris array into chunks of 100
                    let chunk_size = 100;
                    for (let i = 0; i < uris.length; i += chunk_size) {
                        let chunk = uris.slice(i, i + chunk_size);
                        $.ajax({
                            url: '/api/spotify/addSongs/' + playlist_id + '/' + chunk.join(','),
                            type: 'GET',
                            success: function (data) {
                                //TODO: print success message
                            },
                            error: function (data) {
                                console.log(data);
                            },
                            async: false
                        });
                    }
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