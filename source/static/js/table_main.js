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
                validator: column.validator,
            };
        });

        console.log('columns', columns);

        // Создание таблицы
        let table = new Tabulator("#table_main", {
            initialSort: [
                {column: "_sum_minus_2", dir: "desc"}, //sort by this first
            ],
            ajaxURL: "/get_data",
            ajaxConfig: "GET",
            columns: columns,
            layout: "fitData",
        });

        // Обработка события cellEdited
        table.on("cellEdited", function (cell) {
            // Получение данных строки
            var data = cell.getRow().getData();

            // Отправка данных на сервер через AJAX
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/test", true);
            xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    // Обработка успешного ответа, если нужно
                    console.log("Данные успешно отправлены на сервер");
                }
            };
            xhr.send(JSON.stringify(data));
        });
    })

