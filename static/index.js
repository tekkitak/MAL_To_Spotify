$().ready(function() {
    let dataTable = $('#openings_table').dataTable({
        ajax: {
            url: "/mal/animeOpList",
            dataSrc: ""
        },
        stateSave: true,
        columns: [
            { 
                data: "title" 
            },
            { 
                data: "op",
                render: (dt, tp, rw) => {
                    out_str = "<ul class='no-style'>";
                    for (let i = 0; i < dt.length; i++) {
                        let name = dt[i].match(/\"(.+?)\"/)[1];
                        out_str += `<li>${name}</li>`;
                    }
                    return out_str+"</ul>";
                }
            },
        ]
    });
});