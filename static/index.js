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
                    button = `<button id='popup-btn-${row.anime_id}' class='btn btn-sm btn-primary popup-btn'>Change</button>`
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


    $('body').on('click', '.popup-btn', function () {
        console.log('clicked');
        //create a popup with selection of songs from spotify (get from our api) and an input field submitting your own link
        let id = $(this).attr('id').split('-')[2];
        let row = dataTable.fnGetData($(this).closest('tr'));
        let popup = `<div class='popup-content'>`;
        popup += `<div class='popup-header'>`;
        popup += `<h3>${row.title}</h3>`;
        popup += `<h5>${row.op_title}</h5>`;
        popup += `<button id='popup-close-btn' class='btn btn-close'>Close</button>`; // Add this line
        popup += `</div>`;
        popup += `<div class='popup-body'>`;
        popup += `<div class='popup-body-left'>`;
        popup += `<iframe src='https://open.spotify.com/embed/track/${row.op_uri.split(':').slice(-1)}' width='300' height='380' frameborder='0' allowtransparency='true' allow='encrypted-media'></iframe>`;
        popup += `</div>`;
        popup += `<div class='popup-body-right'>`;
        popup += `<h4>Search for song</h4>`;
        popup += `<input type='text' class='form-control' id='popup-search-input' placeholder='Search for song'>`;
        popup += `<div id='popup-search-results'></div>`;
        popup += `<h4>Or submit your own link</h4>`;
        popup += `<input type='text' class='form-control' id='popup-link-input' placeholder='Spotify link'>`;
        popup += `</div>`;
        popup += `</div>`;
        popup += `<div class='popup-footer'>`;
        popup += `<button id='popup-submit-btn' class='btn btn-primary'>Submit</button>`;
        popup += `</div>`;
        popup += `</div>`;
        $('#popup').html(popup);
        $('#popup').show();

        $('#popup-submit-btn').on('click', () => {
            let link = $('#popup-link-input').val();
            if (link != '') {
                $.ajax({
                    url: '/api/mal/updateOp/' + id + '/' + link,
                    type: 'GET',
                    success: function (data) {
                        $('#popup').hide();
                        dataTable.fnReloadAjax();
                    },
                    error: function (data) {
                        console.log(data);
                    },
                    async: false
                });
            }
        });

        $('#popup-search-input').on('keyup', () => {
            let query = $('#popup-search-input').val();
            if (query != '') {
                $.ajax({
                    url: '/api/spotify/search/' + query,
                    type: 'GET',
                    success: function (data) {
                        let results = data.tracks.items;
                        let out = '';
                        for (let i = 0; i < results.length; i++) {
                            out += `<div class='popup-search-result' data-uri='${results[i].uri}'>`;
                            out += `<div class='popup-search-result-left'>`;
                            out += `<img src='${results[i].album.images[2].url}' alt='album cover'>`;
                            out += `</div>`;
                            out += `<div class='popup-search-result-right'>`;
                            out += `<h5>${results[i].name}</h5>`;
                            out += `<p>${results[i].artists[0].name}</p>`;
                            out += `</div>`;
                            out += `</div>`;
                        }
                        $('#popup-search-results').html(out);
                        $('.popup-search-result').on('click', function () {
                            $('#popup-link-input').val($(this).attr('data-uri'));
                        });
                    },
                    error: function (data) {
                        console.log(data);
                    },
                    async: false
                });
            }
        });


        $('#popup-close-btn').on('click', () => {
            $('#popup').hide();
        });


    });


});