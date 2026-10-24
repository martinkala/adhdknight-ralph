// Day screen: deleting a day needs two confirmations (food-004 FR-4).
// The second one only enables the submit button when the typed date matches exactly
// (the Django view checks the match again).
(function () {
    var first = document.getElementById('delete-day-dialog-1');
    var second = document.getElementById('delete-day-dialog-2');
    if (!first || !second) return;
    var input = second.querySelector('[data-testid="delete-day-confirm-input"]');
    var submit = second.querySelector('[data-testid="delete-day-submit"]');

    function syncSubmit() {
        submit.disabled = input.value.trim() !== input.dataset.expected;
    }

    document.querySelector('[data-testid="delete-day"]').addEventListener('click', function () {
        first.showModal();
    });
    first.querySelector('[data-testid="delete-day-cancel-1"]').addEventListener('click', function () {
        first.close();
    });
    first.querySelector('[data-testid="delete-day-continue"]').addEventListener('click', function () {
        first.close();
        input.value = '';
        syncSubmit();
        second.showModal();
        input.focus();
    });
    second.querySelector('[data-testid="delete-day-cancel-2"]').addEventListener('click', function () {
        second.close();
    });
    input.addEventListener('input', syncSubmit);
})();
