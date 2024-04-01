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
            data: {
                watching: true,
                completed: true,
                on_hold: false,
                dropped: false,
                plan_to_watch: false
            },
            traditional: true,
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
                    out = `<div class='custom-modal d-flex flex-row justify-content-between'>`
                    button = `<button id='custom-modal-btn-${row.op_id}' class='btn btn-sm btn-outline-primary custom-modal-btn'>Change</button>`
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
                        return `<input type='checkbox' class='form-check-input border border-danger disabled bg-danger-subtle' name='${row.op_uri}' disabled='true'>`
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
                    if (typeof playlist_id === 'object') {
                        // FIXME: Hacknuté ať to funguje ale jestli tohle čte oponent tak si to vyřiďte s Matějem...
                        playlist_id = playlist_id.id;
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


    $('body').on('click', '.custom-modal-btn', function () {
        let id = $(this).attr('id').split('-')[3];
        let row = dataTable.fnGetData($(this).closest('tr'));
        if (row.op_uri == null) {
            row.op_uri = '';
            row.op_title = '';
            row.op_artist = '';
        }
        let modal = `
                    <div class='custom-modal-content w-100'>
                        <div class='custom-modal-header d-flex w-100 justify-content-between'>
                            <div class='custom-modal-header-left'>
                                <h3>${row.title}</h3>
                                <h5>${row.op_title}</h5>
                            </div>
                            <div class='custom-modal-header-right align-self-right'>
                                <input type='button' class='btn btn-sm btn-danger' id='custom-modal-close-btn' value='Close'>
                            </div>
                        </div>
                    <div class='custom-modal-body'>
                        <div class='custom-modal-body-top d-flex'>
                            <div class='custom-modal-body-left'>`;
                                if (row.op_uri == '') { //TODO: add custom anime-themed image
                                    modal += `<img src='/static/error_img.jpg' alt='Not found image' width="300px">`;
                                } else {
                                    modal +=`<iframe src='https://open.spotify.com/embed/track/${row.op_uri.split(':').slice(-1)}' width='300'
                                    height='380' frameborder='0' allowtransparency='true' allow='encrypted-media'></iframe>`;
                                }
                                modal +=`</div>
                            <div class='custom-modal-body-right m-3 flex-grow-1'>
                                <h5>Suggestions</h5>
                                <table class='w-100'>
                                    <colgroup>
                                        <col span='1' >
                                        <col span='1' style='width: 100%;'>
                                        <col span='1' >
                                        <col span='1' >
                                        <col span='1' >
                                    </colgroup>
                                `
                                $.ajax({
                                    url: '/api/suggestions/getSuggestions/' + id,
                                    type: 'GET',
                                    success: function (data) {
                                        suggestions = JSON.parse(data);
                                        suggestions.forEach( function( suggestion, index ) {
                                            upvotes = suggestion.votes??0;
                                            modal +=`
                                            <tr>
                                            <td>${upvotes}</td>
                                            <td><a href="${suggestion.spotify_link}">${suggestion.song_title} by ${suggestion.artist}</a></td>
                                            <td><button id='suggestion-select-btn-${index}' class='btn btn-sm btn-outline-primary custom-modal-suggestion-btn suggestion-select-btn' data-uri='${suggestion.spotify_link}' data-op='${id}'>
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-box-arrow-in-left" viewBox="0 0 16 16">
                                                    <path fill-rule="evenodd" d="M10 3.5a.5.5 0 0 0-.5-.5h-8a.5.5 0 0 0-.5.5v9a.5.5 0 0 0 .5.5h8a.5.5 0 0 0 .5-.5v-2a.5.5 0 0 1 1 0v2A1.5 1.5 0 0 1 9.5 14h-8A1.5 1.5 0 0 1 0 12.5v-9A1.5 1.5 0 0 1 1.5 2h8A1.5 1.5 0 0 1 11 3.5v2a.5.5 0 0 1-1 0z"/>
                                                    <path fill-rule="evenodd" d="M4.146 8.354a.5.5 0 0 1 0-.708l3-3a.5.5 0 1 1 .708.708L5.707 7.5H14.5a.5.5 0 0 1 0 1H5.707l2.147 2.146a.5.5 0 0 1-.708.708z"/>
                                                </svg>
                                            </button></td>
                                            <td><button id='suggestion-upvote-btn-${index}' class='btn btn-sm btn-outline-primary custom-modal-suggestion-btn suggestion-upvote-btn' data-uri='${suggestion.spotify_link}' data-sid='${suggestion.song_id}'>
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-arrow-up" viewBox="0 0 16 16">
                                                    <path d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"/>
                                                </svg>
                                            </button></td>
                                            <td><button id='suggestion-downvote-btn-${index}' class='btn btn-sm btn-outline-primary custom-modal-suggestion-btn suggestion-downvote-btn' data-uri='${suggestion.spotify_link}' data-sid='${suggestion.song_id}'>
                                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16">
                                                    <path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"/>
                                                </svg>
                                            </button></td>
                                            <td class='d-none'>${suggestion.song_title}</td>
                                            <td class='d-none'>${suggestion.artist}</td>
                                            </tr>`
                                        });

                                    },
                                    error: function (data) {
                                        console.log(data);
                                    },
                                    async: false
                                });
                                modal +=
                                `</table>
                            </div>
                        </div>

                        <div class='custom-modal-body-bottom'>
                        </div>

                        <div class='custom-modal-footer'>
                            <div class='song-submit input-group mb-3'>
                                <span class='input-group-text'>Submit your own link</span>
                                <div class='form-floating'>
                                    <input type='text' class='form-control' id='custom-modal-link-input' placeholder='Spotify link'>
                                    <label for='custom-modal-link-input'>Spotify link</label>
                                </div>
                                <button id='custom-modal-submit-btn' class='btn btn-primary input-group-text'>Submit</button>
                            </div>
                        </div>
                    </div>
                    `;
        $('#custom-modal').html(modal);
        $('#custom-modal').show();

        $('#custom-modal-submit-btn').on('click', () => {
            let link = $('#custom-modal-link-input').val();
            $.ajax({
                url: '/api/suggestions/addSuggestion',
                data: JSON.stringify({
                    opening_id: id,
                    spotify_uri: link
                }),
                contentType: 'application/json',
                type: 'POST',
                success: function (data) {
                    $('#custom-modal').hide();
                },
                error: function (data) {
                    console.log(data);
                },
                async: false
            });
        });

        $('#custom-modal-search-input').on('keyup', () => {
            let query = $('#custom-modal-search-input').val();
            if (query != '') {
                $.ajax({
                    url: '/api/spotify/search/' + query,
                    type: 'GET',
                    success: function (data) {
                        let results = data.tracks.items;
                        let out = '';
                        for (let i = 0; i < results.length; i++) {
                            out += `<div class='custom-modal-search-result' data-uri='${results[i].uri}'>`;
                            out += `<div class='custom-modal-search-result-left'>`;
                            out += `<img src='${results[i].album.images[2].url}' alt='album cover'>`;
                            out += `</div>`;
                            out += `<div class='custom-modal-search-result-right'>`;
                            out += `<h5>${results[i].name}</h5>`;
                            out += `<p>${results[i].artists[0].name}</p>`;
                            out += `</div>`;
                            out += `</div>`;
                        }
                        $('#custom-modal-search-results').html(out);
                        $('.custom-modal-search-result').on('click', function () {
                            $('#custom-modal-link-input').val($(this).attr('data-uri'));
                        });
                    },
                    error: function (data) {
                        console.log(data);
                    },
                    async: false
                });
            }
        });


        $('#custom-modal-close-btn').on('click', () => {
            $('#custom-modal').hide();
        });


    });

    //FIXME: fix the bug where while updating the row the data from the previous row is suddenly disappearing
    $('body').on('click', '.suggestion-select-btn', function () {
        spotify_uri = $(this).attr('data-uri');
        song_index = $(this).attr('id').split('-')[3];
        opening_id = $(this).attr('data-op');

        let row = dataTable.fnGetData($('#custom-modal-btn-' + opening_id).closest('tr'));
        console.log(row);
        row.op_uri = spotify_uri;

        new_op_title = row.op_title;
        if (row.op_title.includes('(')) {
            new_op_title = row.op_title.split('(')[0] + '(' + $('#suggestion-select-btn-' + song_index).closest('tr').find('td:nth-child(6)').text() + ')';
        } else {
            new_op_title = row.op_title + ' (' + $('#suggestion-select-btn-' + song_index).closest('tr').find('td:nth-child(6)').text() + ')';
        }
        row.op_title = new_op_title;

        new_op_artist = row.op_artist;
        if (row.op_artist.includes('(')) {
            new_op_artist = row.op_artist.split('(')[0] + '(' + $('#suggestion-select-btn-' + song_index).closest('tr').find('td:nth-child(7)').text() + ')';
        } else {
            new_op_artist = row.op_artist + ' (' + $('#suggestion-select-btn-' + song_index).closest('tr').find('td:nth-child(7)').text() + ')';
        }
        row.op_artist = new_op_artist;

        dataTable.fnUpdate(row, $('#custom-modal-btn-' + opening_id).closest('tr'));
        $('#custom-modal').hide();
    });

    async function vote (id, vote) {
        $.ajax({
            url: '/api/suggestions/vote',
            data: JSON.stringify({
                song_id: id,
                vote: vote
            }),
            contentType: 'application/json',
            type: 'POST',
            success: function (data) {
                console.log(data);
            },
            error: function (data) {
                console.log(data);
            },

        })
    }

    $('body').on('click', '.suggestion-upvote-btn', function () {
        suggestion_id = $(this).attr('data-sid');
        vote(suggestion_id, 1);
    });

    $('body').on('click', '.suggestion-downvote-btn', function () {
        suggestion_id = $(this).attr('data-sid');
        vote(suggestion_id, -1);
    });



});
