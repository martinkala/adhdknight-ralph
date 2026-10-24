// Common medication + supplement input (food-007 FR-3).
// - An answer with unknown items swaps in the "medication or supplement?" dialog ([data-classify-dialog]);
//   it opens as a modal. Each item needs a choice before Save is enabled.
// - Cancel (or Esc) closes and removes the dialog; the text stays in the quick add field.
// - A successful save from the dialog clears the quick add field and focuses it for the next item.
(function () {
    function medsField() {
        return document.querySelector('form[data-meds-form] input[name=text]');
    }

    var focusAfterSwap = false;

    document.body.addEventListener('htmx:afterSettle', function () {
        if (focusAfterSwap) {
            focusAfterSwap = false;
            var field = medsField();
            if (field) field.focus();
        }
        var dialog = document.querySelector('dialog[data-classify-dialog]:not([open])');
        if (dialog) {
            dialog.showModal();
            var first = dialog.querySelector('.kind-btn');
            if (first) first.focus();
        }
    });

    // `close` does not bubble: listen in the capture phase.
    document.addEventListener('close', function (event) {
        var dialog = event.target;
        if (!dialog.matches || !dialog.matches('dialog[data-classify-dialog]')) return;
        dialog.remove();
        var field = medsField();
        if (field) field.focus();
    }, true);

    document.body.addEventListener('click', function (event) {
        var button = event.target.closest('[data-classify-dialog] .kind-btn');
        if (button) {
            var row = button.closest('.classify-row');
            row.querySelector('[data-classify-kind]').value = button.dataset.kind;
            row.querySelectorAll('.kind-btn').forEach(function (b) {
                b.setAttribute('aria-pressed', b === button ? 'true' : 'false');
            });
            var form = button.closest('form');
            var done = Array.prototype.every.call(form.querySelectorAll('[data-classify-kind]'), function (input) {
                return input.value !== '';
            });
            form.querySelector('[type=submit]').disabled = !done;
            return;
        }
        var cancel = event.target.closest('[data-classify-cancel]');
        if (cancel) cancel.closest('dialog').close();
    });

    // htmx:beforeSwap still fires inside the document (the dialog and its form are replaced by the swap).
    document.body.addEventListener('htmx:beforeSwap', function (event) {
        var form = event.detail.requestConfig && event.detail.requestConfig.elt;
        if (!form || !form.matches || !form.matches('form[data-classify-form]')) return;
        var xhr = event.detail.xhr;
        if (xhr.status !== 200 || xhr.getResponseHeader('X-Food-Error') || xhr.getResponseHeader('X-Food-Keep-Input')) return;
        var field = medsField();
        if (field) field.value = '';
        // The modal dialog keeps the rest of the page inert until it is swapped out.
        focusAfterSwap = true;
    });
})();
