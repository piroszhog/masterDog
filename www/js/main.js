var miners = [];
var dogs = [];

// {'miner1Name': jqueryObject1, 'miner2Name': jqueryObject2, ...}
var drawnCards = {};
var drawnRows = {};

//
// Templates
//

function alertTemplate(text, status) {
    var html =
        '<div class="alert alert-' + status + '">' +
            '<div class="alert-content-wrapper">' +
                text +
            '</div>' +
        '</div>';

    return html;
}

function cardTemplate(miner) {
    var html = '<div id="card' + miner.name + '" class="card miner-card">' +
        '<div class="card-area-main">' +
            '<div class="card-title-primary">' +
                '<div class="card-title-box">' +
                    '<div class="card-title-primary-text">' +
                        miner.name +
                    '</div>' +
                '<div class="card-subtitle-primary-text">' +
                    miner.ip +
                '</div>' +
            '</div>' +
        '</div>' +
        dogSelectTemplate() +
    '</div>';

    return html;
}

function dogSelectTemplate() {
    var html =
        '<div class="card-content">' +
            '<div class="select-box">' +
                '<select class="dog-select">' +
                    '<option selected="true" disabled>' + 'Choose dog' + '</option>';

    $.each(dogs, function(index, dog) {
        html += '<option value="' + dog.localIP +'">' + dog.localIP + '</option>';
    });

    html += '</select></div></div>';
    return html;
}

function buttonTemplate(buttonText) {
    var html =
        '<div class="buttons-group-item ' + buttonText + '">' +
            '<button class="button button-flat">' +
                '<div class="button-text">' + buttonText + '</div>' +
            '</button>' +
        '</div>';
    return html;
}

function buttonsGroupTemplate(buttonsTexts) {
    var html = '<td><div class="buttons-group">';
    for(var i=0; i<buttonsTexts.length; i++)
        html += buttonTemplate(buttonsTexts[i]);
    html += '</div></td>';
    return html;
}

function dogTableHeadTemplate() {
    var html =
        '<thead><tr>' +
            '<td class="column-header">name</td>' +
            '<td class="column-header">IP</td>' +
            '<td class="column-header">dog port</td>' +
            '<td class="column-header">powered on</td>' +
            '<td class="column-header">last share</td>' +
            '<td class="column-header"></td>' +
        '</tr></thead>';
    return html;
}

function dogTableRowTemplate(minerFromDogState) {
    var html =
        '<tr id="row' + minerFromDogState.name + '" </td>' +
            '<td class="name">' + minerFromDogState.name + '</td>' +
            '<td class="host">' + minerFromDogState.host + '</td>' +
            '<td class="port">' + minerFromDogState.mp710_port + '</td>' +
            '<td class="powered">' + minerFromDogState.last_power_on_date + '</td>' +
            '<td class="submitted">' + minerFromDogState.last_submitted_date + '</td>' +
            buttonsGroupTemplate(['unbind']) +
        '</tr>';
    return html;
}

function dogTableTemplate(dog) {
    var html =
        '<div id="dog' + dog.localIP.split('.').join("") + '" class="dog-table-wrapper">' +
            '<div class="dog-table-title">' +
                'Watchdog ' + dog.localIP +
            '</div>' +
            '<table class="data-table">' +
                dogTableHeadTemplate() +
                '<tbody>';
    
    html += '</tbody></table></div>';
    return html;
}

function dogsTablesListTemplate() {
    var html =
        '<div class="tables-list">' +
			'<div class="centering-wrapper">' +
            '</div>' +
        '</div>';
    return html;
}



//
// UI functions
//

function removeObjectByTimeout(jqueryObject, timeout) {
    setTimeout(function removeObjectByTimeout() {
        jqueryObject.remove();
    }, timeout);
}

// status = 'success' or 'error'
function showAlert(text, status) {
    removeObjectByTimeout($(alertTemplate(text, status)).appendTo('.alerts-wrapper'), 3000);
}

function redrawCard(miner) {
    $('#card' + miner.name).find('.card-subtitle-primary-text').html(miner.ip);
}

function drawCard(miner) {
    if(miner.dog_ip)
        return false;

    var isNewMiner = true;
    for(var i=0; i<miners.length; i++)
        if(miner.name == miners[i].name) {
            isNewMiner = false;
            break;
        }

    if(isNewMiner) {
        miners.push(miner);
        drawnCards[miner.name] = $(cardTemplate(miner)).appendTo('.miner-wrapper');

        //Register new events for selects
        selectOnChangeListener(drawnCards[miner.name]);
    }
    else
        redrawCard(miner);
}

function redrawDogsSelects() {
    $.each(miners, function(index, miner) {
        var card = $('#card' + miner.name);
        card.find('.card-content').remove();
        card.append(dogSelectTemplate());
        selectOnChangeListener(card);
    });
}

function redrawTableRow(minerFromDogState) {
    var row = $('#row' + minerFromDogState.name);
    row.find('.name').html(minerFromDogState.name);
    row.find('.host').html(minerFromDogState.host);
    row.find('.port').html(minerFromDogState.mp710_port);
    row.find('.powered').html(minerFromDogState.last_power_on_date);
    row.find('.submitted').html(minerFromDogState.last_submitted_date);
}

function drawDogsWrapper() {
    $('.body-wrapper').append(dogsTablesListTemplate());
}

function drawTableRow(jqueryTableObject, miner){
    drawnRows[miner.name] = $(dogTableRowTemplate(miner)).appendTo(jqueryTableObject.find('tbody'));
    drawnRows[miner.name].find('.unbind').click(function(){unbindMiner(miner.name);});
}

function drawDogTable(dog) {
    var table = $(dogTableTemplate(dog)).appendTo('.centering-wrapper');
    $.each(dog.miners, function(index, miner) {
        drawTableRow(table, miner);
    });
}

function drawDogsTables() {
    for(var i=0; i<dogs.length; i++) {
        var table = $('#dog' + dogs[i].localIP.split('.').join(""));
        
        if(!table.length)
            drawDogTable(dogs[i]);
        else
            $.each(dogs[i].miners, function (index, miner) {
                if (drawnRows[miner.name])
                    redrawTableRow(miner);
                else
                    drawTableRow(table, miner);
            });
    }
}

function removeCardsOfAbsentMiners() {
    $.each(drawnCards, function(minerName, drawnObject) {
        minerFound = false;
        for (var i = 0; i < miners.length; i++)
            if (minerName == miners[i].name)
                minerFound = true;

        if (!minerFound) {
            drawnObject.remove();
            delete drawnCards[minerName];
        }
    });
}

function removeRowsOfAbsentMiners() {
    $.each(drawnRows, function(minerName, drawnObject){
        minerFound = false;
        for(var j=0; j<dogs.length; j++) {
            for (var i = 0; i < dogs[j].miners.length; i++)
                if (minerName == dogs[j].miners[i].name) {
                    minerFound = true;
                    break;
                }

            if(minerFound)
                break;
        }

        if (!minerFound) {
            drawnObject.remove();
            delete drawnRows[minerName];
        }
    });
}



//
// Logical functions
//

function findMiner(minerName) {
    for(var i=0; i<miners.length; i++)
        if(miners[i].name == minerName)
            return miners[i];
    return false
}

function bindMiner(minerName, dogIP) {
    if(!dogIP || !minerName) {
        showAlert('You must set minerName and dogIP to bind miner!', 'error');
        return false;
    }

    $.ajax({url: "/bind?name=" + minerName + "&dogIP=" + dogIP, method: "GET"})
        .done(function(data) {
            showAlert('Miner ' + minerName + ' bound to dog ' + dogIP, 'success');
            return true;
        })
        .fail(function() {
            showAlert('Can not bind ' + minerName + ' to dog ' + dogIP, 'error');
            return false;
        });
}

function unbindMiner(minerName) {
    $.ajax({url: "/unbind?name=" + minerName, method: "GET"})
        .done(function() {
            showAlert('Miner ' + minerName + ' unbound from dog', 'success');
            return true;
        })
        .fail(function() {
            showAlert('Can not unbind ' + minerName + ' from dog', 'error');
            return false;
        });
}

function selectOnChangeListener(jqueryObjectOfCard) {
    jqueryObjectOfCard.find('.dog-select').change(function() {
        bindMiner(
            $(this).closest('.miner-card').find('.card-title-primary-text').html(),
            $(this).val());
    });
}




//
// Entry points
//

$(document).ready(function() {

    drawDogsWrapper();

    (function get_miners() {
        setTimeout(function()
        {
            $.ajax({url: "/miners", method: "GET"})
                .done(function(data) {
                    var actualMiners = data.miners;
                    $.each(actualMiners, function(index, miner) {
                        drawCard(miner);
                    });
                    miners = actualMiners;
                    removeCardsOfAbsentMiners();
                })
                .always(get_miners());
        }, 1000);
    })();

    (function get_dogs() {
        setTimeout(function() {
            $.ajax({url: "/dogs", method: "GET"})
                .done(function(data) {
                    var actualDogs = data.dogs;
                    if(actualDogs.length != dogs.length) {
                        dogs = actualDogs;
                        redrawDogsSelects();
                        drawDogsTables();
                    }
                    else {
                        dogs = actualDogs;
                        drawDogsTables();
                    }
                    removeRowsOfAbsentMiners();
                })
                .always(get_dogs());
        }, 1000);
    })();
});
