// Day screen entries and measurements (food-005 FR-3, FR-4).
// - Quick add forms ([data-quick-add]) are cleared as soon as the request is sent, so the next item
//   can be typed right away; focus stays in the field. A failed save (X-Food-Error) puts the text back.
// - Textareas with [data-enter-submits]: Enter saves, Shift+Enter is a new line.
// - Tapping an entry text ([data-edit-toggle]) switches its row to the inline edit form; Esc cancels.
// - The quantity popover closes with its Close button or Esc.
(function () {
    function fields(form) {
        return Array.prototype.slice.call(form.querySelectorAll('input:not([type=hidden]), textarea'));
    }

    document.body.addEventListener('htmx:configRequest', function (event) {
        var form = event.detail.elt;
        if (!form.matches || !form.matches('form[data-quick-add]')) return;
        // Parameters are already collected; clear the fields for the next item.
        form._sent = fields(form).map(function (field) {
            var value = field.value;
            field.value = '';
            return value;
        });
    });

    document.body.addEventListener('htmx:afterRequest', function (event) {
        var form = event.detail.elt;
        if (!form.matches || !form.matches('form[data-quick-add]') || !form._sent) return;
        var xhr = event.detail.xhr;
        // X-Food-Keep-Input: saved nothing yet, a question follows (food-007 classification dialog).
        var failed = !event.detail.successful ||
            (xhr && (xhr.getResponseHeader('X-Food-Error') || xhr.getResponseHeader('X-Food-Keep-Input')));
        if (failed) {
            var list = fields(form);
            var untouched = list.every(function (field) { return field.value === ''; });
            if (untouched) {
                list.forEach(function (field, i) { field.value = form._sent[i]; });
            }
        }
        form._sent = null;
    });

    function startEdit(row) {
        document.querySelectorAll('.entry-row.editing').forEach(cancelEdit);
        row.classList.add('editing');
        var field = row.querySelector('.edit-form input, .edit-form textarea');
        field.focus();
        if (field.select) field.select();
    }

    function cancelEdit(row) {
        row.classList.remove('editing');
        row.querySelector('.edit-form').reset();
    }

    document.body.addEventListener('click', function (event) {
        var toggle = event.target.closest('[data-edit-toggle]');
        if (toggle) {
            startEdit(toggle.closest('.entry-row'));
            return;
        }
        var close = event.target.closest('[data-popover-close]');
        if (close) close.closest('.qty-popover-slot').innerHTML = '';
    });

    document.body.addEventListener('keydown', function (event) {
        var target = event.target;
        if (event.key === 'Enter' && !event.shiftKey && target.matches('textarea[data-enter-submits]')) {
            event.preventDefault();
            target.form.requestSubmit();
        } else if ((event.key === 'Enter' || event.key === ' ') && target.matches('[data-edit-toggle]')) {
            event.preventDefault();
            startEdit(target.closest('.entry-row'));
        } else if (event.key === 'Escape') {
            var row = target.closest('.entry-row.editing');
            if (row) cancelEdit(row);
            var slot = target.closest('.qty-popover-slot');
            if (slot) slot.innerHTML = '';
        }
    });
})();
