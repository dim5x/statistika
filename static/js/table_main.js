fetch('/get_columns')
    .then(response => {
        if (response.ok) {
            return response.json();
        }
        throw new Error('Network response was not ok.');
    })
    .then(data => {
        // Создание массива объектов столбцов на основе полученных данных
        let serverColumns = data;
        console.log('serverColumns', serverColumns);
        // Создание столбцов в таблице Tabulator на основе serverColumns
        let columns = serverColumns.map(column => {
            return {
                title: column.title,
                field: column.field,
                editor: column.editor,
                // Другие параметры столбца, если необходимо
                hozAlign: column.hozAlign,
                sorter: column.sorter,
                // dir: column.dir
            };
        });

        console.log('columns', columns);

        // Создание таблицы
        // let table = new Tabulator("#table_main", {
        new Tabulator("#table_main", {

            initialSort: [
                {column: "summa_2", dir: "desc"}, //sort by this first
            ],
            ajaxURL: "/get_data_for_main_table",
            ajaxConfig: "GET",
            columns: columns,
            layout: "fitData",

            ajaxResponse: function (url, params, response) {
                return response;
            },
        });
    })
