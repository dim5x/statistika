// Установить активную вкладку при загрузке страницы
// Установить активную вкладку при загрузке страницы
document.addEventListener("DOMContentLoaded", function (event) {
    // Выберите вкладку, которую хотите сделать активной
    var defaultTab = document.getElementById('main_table_link'); // Например, установим Tab 2 активной

    // Пометить выбранную вкладку как активную
    defaultTab.click();
});

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
                // accessor: function (data) {
                //     return data[column.field];
                // },
                field: column.field,
                editor: column.editor
                // Другие параметры столбца, если необходимо
            };

        });

        console.log('columns', columns);
// Создание таблицы
        let table = new Tabulator("#table_main", {
            ajaxURL: "/get_data_for_main_table",
            ajaxConfig: "GET",
            columns: columns,
            layout: "fitData",

            ajaxResponse: function (url, params, response) {
                return response;
            },
        });
    })


