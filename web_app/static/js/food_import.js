// Import preview (food-011 FR-4).
// - Each conflict and each unknown medication item is a row with a choice ([data-choice-row]);
//   a tap stores the choice in the row's hidden input ([data-choice-input]).
// - "Use for all" copies the last chosen conflict answer to every conflict.
// - Import is enabled only when every row has a choice.
(function () {
    var form = document.querySelector('form[data-import-form]');
    if (!form) return;
    var lastConflictChoice = '';

    function choose(row, value) {
        row.querySelector('[data-choice-input]').value = value;
        row.querySelectorAll('[data-choice]').forEach(function (b) {
            b.setAttribute('aria-pressed', b.dataset.choice === value ? 'true' : 'false');
        });
    }

    function update() {
        var commit = form.querySelector('[data-import-commit]');
        if (!commit) return;
        var done = Array.prototype.every.call(form.querySelectorAll('[data-choice-input]'), function (input) {
            return input.value !== '';
        });
        commit.disabled = !done || !form.querySelector('[data-testid=import-day]');
        var applyAll = form.querySelector('[data-apply-all]');
        if (applyAll) applyAll.disabled = lastConflictChoice === '';
    }

    form.addEventListener('click', function (event) {
        var button = event.target.closest('[data-choice-row] [data-choice]');
        if (button) {
            var row = button.closest('[data-choice-row]');
            choose(row, button.dataset.choice);
            if (row.matches('[data-testid=import-conflict]')) lastConflictChoice = button.dataset.choice;
            update();
            return;
        }
        if (event.target.closest('[data-apply-all]') && lastConflictChoice) {
            form.querySelectorAll('[data-testid=import-conflict]').forEach(function (row) {
                choose(row, lastConflictChoice);
            });
            update();
        }
    });

    update();
})();
