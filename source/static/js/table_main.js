// var cellContextMenu = [
//     {
//         label: "Reset Value",
//         action: function (e, cell) {
//             cell.setValue("");
//         }
//     },
// ]
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
                // contextMenu:cellContextMenu
                validator: column.validator
            };
        });

        console.log('columns', columns);

        // Создание таблицы
        // let table = new Tabulator("#table_main", {
        new Tabulator("#table_main", {

            initialSort: [
                {column: "_sum_minus_2", dir: "desc"}, //sort by this first
            ],
            ajaxURL: "/get_data",
            ajaxConfig: "GET",
            columns: columns,
            layout: "fitData",

            ajaxResponse: function (url, params, response) {
                return response;
            },
        });
    })

function sendDataToUpdate(data) {
    fetch('/test', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Network response was not ok.');
        })
        .then(data => {
            console.log(data); // Обработка успешного ответа от сервера
            // Дополнительная обработка данных при необходимости
        })
        .catch(error => {
            console.error('Fetch error:', error); // Обработка ошибок
        });
}