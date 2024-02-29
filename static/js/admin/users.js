$().ready(function() {
    var table = $('#users').DataTable({
        ajax: {
            url: "/api/admin/getUsers",
            data: function (d) {
                d.offset = d.start;
                d.limit = d.length;
            },
            dataFilter: function(data) {
                var json = jQuery.parseJSON(data);
                json.recordsFiltered = json.recordsTotal;
                return JSON.stringify(json);
            }
        },
        processing: true,
        serverSide: true,
        columns: [
            {
                title: 'ID',
                data: 'id',
            },
            {
                title: 'Username',
                data: 'username',
            },
            {
                title: 'Email',
                data: 'email',
            },
            {
                title: 'Roles',
                data: 'roles',
                render: function (data, type, row) {
                    out='';
                    for (var i = 0; i < row.roles.length; i++) {
                        out += row.roles[i].name + ' ';
                    }
                    return out;
                }
            },
            {
                title: 'Actions',
                data: null,
                render: function (data, type, row) {
                    return '<a href="/admin/users/' + row.id + '" class="btn btn-primary">Edit</a>';
                }
            },
        ],
    });

});
