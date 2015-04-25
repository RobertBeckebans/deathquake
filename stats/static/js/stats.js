"use strict";
//TODO: Convert to pairs or something even prettier!
var COLUMN_NAMES = [
    '#'
    , ''
    , 'Name'
    , 'Score'
    , 'Score 14'
    , 'Difference'
    , '<span class="icon icon-kills"></span>'
    , '<span class="icon icon-deaths"></span>'
    , '<span class="icon icon-kills"></span>:<span class="icon icon-deaths"></span>'
    , '<span class="icon icon-rocket-kills"></span>'
    , '<span class="icon icon-railgun-kills"></span>'
    , '<span class="icon icon-gauntlet-kills"></span>'
    , '<span class="icon icon-highest-kill-streak"></span>'
    , '<span class="icon icon-fall-deaths"></span>'
    , '<span class="icon icon-won-rounds"></span>'];
var COLUMN_ID = [
    'rank'
    , 'rank_difference'
    , 'name'
    , 'score'
    , 'score_14'
    , 'score_14_difference'
    , 'kills'
    , 'deaths'
    , 'kill_death_ratio'
    , 'rocket_kills'
    , 'railgun_kills'
    , 'gauntlet_kills'
    , 'highest_kill_streak'
    , 'fall_deaths'
    , 'won_games'];

var isScoreboardCreated = false;
var numberOfRows = 0;

$(document).ready(
    setInterval(function () {
        $.getJSON('scoreboard.json', function (rootNode) {
            var status = rootNode[0].status;
            var data = rootNode[1].data;
            var log = rootNode[2].log;
            if (status == 'success') {
                var numberOfPlayers = 0;
                if (!isScoreboardCreated) createScoreboard();
                $.each(data, function (id, player) {
                    updateOrInsertPlayer(player);
                    numberOfPlayers++;
                });
                removeExtraRows(numberOfPlayers);
            } else if (status == 'failed') {
                $('#scoreboard').html(status);
            }

            if (log) {
                $("#log").html(log);
            }
        });
    }, 1000)
);

var createScoreboard = function () {
    var $scoreboard = $('#scoreboard');
    $scoreboard.html('');
    $scoreboard.append('<table id="scoreboard_table" class="table table-condensed">');
    var $scoreboardTable = $('#scoreboard_table');
    $scoreboardTable.append('<tr>');
    $.each(COLUMN_ID, function (column) {
        $scoreboardTable.find('tr').append('<th class="' + COLUMN_ID[column] + '">' + COLUMN_NAMES[column] + '</th>');
    });
    isScoreboardCreated = true;
};

var updateOrInsertPlayer = function (player) {
    createEnoughRows(player);
    var row = $("#rank_" + player['rank']);
    updateColumn(row, 'name', player['name']);
    updateColumn(row, 'rank', player['rank']);
    updateColumn(row, 'rank_difference', prettyRankDifference(player));
    updateColumn(row, 'score', player['score']);
    updateColumn(row, 'score_14', player['score_14']);
    updateColumn(row, 'score_14_difference', player['score_14_difference']);
    updateColumn(row, 'kills', player['kills']);
    updateColumn(row, 'deaths', player['deaths']);
    updateColumn(row, 'kill_death_ratio', player['kill_death_ratio']);
    updateColumn(row, 'railgun_kills', player['railgun_kills']);
    updateColumn(row, 'highest_kill_streak', player['highest_kill_streak']);
    updateColumn(row, 'rocket_kills', player['rocket_kills']);
    updateColumn(row, 'fall_deaths', player['fall_deaths']);
    updateColumn(row, 'gauntlet_kills', player['gauntlet_kills']);
    updateColumn(row, 'won_games', player['won_games']);
    assignColors(player, row);
};

var createEnoughRows = function (player) {
    var $scoreboardTable = $('#scoreboard_table');
    while (player['rank'] > numberOfRows) {
        $scoreboardTable.append('<tr id="rank_' + (numberOfRows + 1) + '"></tr>');
        numberOfRows++;
        $.each(COLUMN_ID, function (column) {
            var $rankRow = $('#rank_' + numberOfRows);
            $rankRow.append('<td class="' + COLUMN_ID[column] + '"></td>');
        });
    }
};

var updateColumn = function (row, column, value) {
    row.find('td.' + column).html(value);
};

var prettyRankDifference = function (player) {
    var rank_difference = player['rank_difference'];
    if (rank_difference != 0) {
        if (rank_difference > 0) {
            return '+' + rank_difference;
        } else {
            return rank_difference;
        }
    } else {
        return '';
    }
};

var assignColors = function (player, row) {
    function enableTrophyIfTrue(trophy) {
        if (player[trophy]) {
            row.addClass(trophy);
        } else {
            row.removeClass(trophy);
        }
    }

    function enableTrophyOnColumnIfTrue(variable, column) {
        var td = row.find('td.' + column);
        if (player[variable]) {
            td.addClass(variable);
        } else {
            td.removeClass(variable);
        }
    }

    var rank_difference = row.find('td.rank_difference');
    if (player['rank_difference'] > 0) {
        rank_difference.removeClass('negative_rank_difference');
        rank_difference.addClass('positive_rank_difference');
    } else if (player['rank_difference'] < 0) {
        rank_difference.removeClass('positive_rank_difference');
        rank_difference.addClass('negative_rank_difference');
    } else {
        rank_difference.removeClass('positive_rank_difference');
        rank_difference.removeClass('negative_rank_difference');
    }
    enableTrophyIfTrue('trophy_winner');
    enableTrophyIfTrue('trophy_won_last_game');
    enableTrophyOnColumnIfTrue('trophy_railgun_kills', 'railgun_kills');
    enableTrophyOnColumnIfTrue('trophy_rocket_kills', 'rocket_kills');
    enableTrophyOnColumnIfTrue('trophy_gauntlet_kills', 'gauntlet_kills');
    enableTrophyOnColumnIfTrue('trophy_fall_deaths', 'fall_deaths');
    enableTrophyOnColumnIfTrue('trophy_highest_kill_streak', 'highest_kill_streak');
    enableTrophyOnColumnIfTrue('trophy_won_games', 'won_games');
    enableTrophyOnColumnIfTrue('trophy_kills', 'kills');
    enableTrophyOnColumnIfTrue('trophy_deaths', 'deaths');
    enableTrophyOnColumnIfTrue('trophy_kill_death_ratio', 'kill_death_ratio');
};

var removeExtraRows = function (number) {
    while (numberOfRows > number) {
        $('#scoreboard_table').find('#rank_' + numberOfRows).remove();
        numberOfRows--;
    }
};