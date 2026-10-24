// Autocomplete of entry texts (food-006 FR-2) on inputs with [data-suggest="<group>"].
// - Quick add fields search the last comma separated part without its leading quantity
//   ("2 toasty, ka" -> "ka"). Choosing a suggestion replaces that part (the quantity stays) and,
//   when the input is a single item, adds it right away; otherwise typing goes on.
// - Inline edit fields ([data-suggest-whole]) search the whole text; choosing saves it.
// - Shows after typing (150 ms debounce) or on focus of an empty field. Arrows + Enter or a tap choose,
//   Esc or leaving the field closes. Enter without a chosen suggestion is the normal add.
(function () {
    var DEBOUNCE_MS = 150;
    // A comma between two digits is a decimal comma (same rule as the server's split_entries).
    var SEPARATOR = /\n|(?<!\d),|,(?!\d)/g;
    // Leading quantity, same forms as the server's parse_quantity: "2 ", "2x ", "1/2 ", "0,5 l ", "200g ".
    var QUANTITY = /^(?:\d+\/\d+|\d+(?:[.,]\d+)?|[.,]\d+)(?:\s*[x×](?=\s|$)|\s*(?:kg|ml|ks|g|l)(?=\s|$)|(?=\s))\s*/i;

    var state = null;  // {input, list, items, active, seq, timer} of the focused field
    var listCounter = 0;

    function limit() {
        return window.matchMedia('(min-width: 600px)').matches ? 10 : 8;
    }

    // value -> {head, query}: head is kept as is, query is what is searched and replaced.
    function split(input) {
        var value = input.value;
        if (input.hasAttribute('data-suggest-whole')) return {head: '', query: value.trim()};
        var start = 0;
        var match;
        SEPARATOR.lastIndex = 0;
        while ((match = SEPARATOR.exec(value)) !== null) start = match.index + match[0].length;
        var part = value.slice(start);
        var lead = part.match(/^\s*/)[0];
        part = part.slice(lead.length);
        var quantity = part.match(QUANTITY);
        var prefix = quantity ? quantity[0] : '';
        return {head: value.slice(0, start) + lead + prefix, query: part.slice(prefix.length), single: !value.slice(0, start).trim()};
    }

    function ensureList(input) {
        if (!input._suggestList) {
            var list = document.createElement('ul');
            list.id = 'suggestions-' + (++listCounter);
            list.className = 'suggestions';
            list.setAttribute('role', 'listbox');
            list.setAttribute('data-testid', 'suggestions');
            list.hidden = true;
            input.insertAdjacentElement('afterend', list);
            input.setAttribute('role', 'combobox');
            input.setAttribute('aria-autocomplete', 'list');
            input.setAttribute('aria-controls', list.id);
            input.setAttribute('aria-expanded', 'false');
            input._suggestList = list;
        }
        return input._suggestList;
    }

    function close() {
        if (!state) return;
        clearTimeout(state.timer);
        state.seq++;
        state.items = [];
        state.active = -1;
        state.list.hidden = true;
        state.list.innerHTML = '';
        state.input.setAttribute('aria-expanded', 'false');
        state.input.removeAttribute('aria-activedescendant');
    }

    function setActive(index) {
        var options = state.list.children;
        if (state.active >= 0 && options[state.active]) options[state.active].setAttribute('aria-selected', 'false');
        state.active = index;
        if (index >= 0) {
            options[index].setAttribute('aria-selected', 'true');
            options[index].scrollIntoView({block: 'nearest'});
            state.input.setAttribute('aria-activedescendant', options[index].id);
        } else {
            state.input.removeAttribute('aria-activedescendant');
        }
    }

    function render(items) {
        var list = state.list;
        list.innerHTML = '';
        state.items = items;
        state.active = -1;
        state.input.removeAttribute('aria-activedescendant');
        if (!items.length) {
            close();
            return;
        }
        items.forEach(function (item, i) {
            var option = document.createElement('li');
            option.id = list.id + '-' + i;
            option.setAttribute('role', 'option');
            option.setAttribute('aria-selected', 'false');
            option.setAttribute('data-testid', 'suggestion');
            option.textContent = item.text;
            list.appendChild(option);
        });
        list.hidden = false;
        state.input.setAttribute('aria-expanded', 'true');
    }

    function load() {
        var input = state.input;
        var current = state;
        var seq = ++state.seq;
        var params = new URLSearchParams({group: input.dataset.suggest, q: split(input).query, limit: limit()});
        fetch(input.dataset.suggestUrl + '?' + params.toString(), {credentials: 'same-origin'})
            .then(function (r) { return r.ok ? r.json() : {suggestions: []}; })
            .then(function (data) {
                if (state === current && seq === current.seq && document.activeElement === input) {
                    render(data.suggestions || []);
                }
            })
            .catch(function () {});
    }

    function schedule(delay) {
        clearTimeout(state.timer);
        state.timer = setTimeout(load, delay);
    }

    function choose(index) {
        var input = state.input;
        var item = state.items[index];
        if (!item) return;
        var parts = split(input);
        input.value = parts.head + item.text;
        close();
        if (input.hasAttribute('data-suggest-whole') || parts.single) {
            input.form.requestSubmit();
        } else {
            input.focus();
            input.setSelectionRange(input.value.length, input.value.length);
        }
    }

    function isSuggestInput(el) {
        return el && el.matches && el.matches('input[data-suggest]') && el.dataset.suggest;
    }

    document.addEventListener('focusin', function (event) {
        var input = event.target;
        if (!isSuggestInput(input)) return;
        if (state && state.input !== input) close();
        state = {input: input, list: ensureList(input), items: [], active: -1, seq: 0, timer: null};
        if (!input.value.trim()) schedule(0);
    });

    document.addEventListener('focusout', function (event) {
        if (state && event.target === state.input) close();
    });

    document.addEventListener('input', function (event) {
        if (state && event.target === state.input) schedule(DEBOUNCE_MS);
    });

    // Capture phase: runs before the Enter / Esc handlers of food_entries.js and the implicit form submit.
    document.addEventListener('keydown', function (event) {
        if (!state || event.target !== state.input) return;
        var open = !state.list.hidden && state.items.length > 0;
        var n = state.items.length;
        if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
            if (!open) {
                schedule(0);
            } else {
                setActive(event.key === 'ArrowDown' ? (state.active + 1) % n : (state.active - 1 + n) % n);
            }
            event.preventDefault();
        } else if (event.key === 'Enter') {
            if (open && state.active >= 0) {
                event.preventDefault();
                event.stopPropagation();
                choose(state.active);
            } else {
                close();
            }
        } else if (event.key === 'Escape' && open) {
            event.preventDefault();
            event.stopPropagation();
            close();
        } else if (event.key === 'Tab') {
            close();
        }
    }, true);

    // Keep the focus in the field while tapping a suggestion.
    document.addEventListener('mousedown', function (event) {
        if (state && event.target.closest('.suggestions') === state.list) event.preventDefault();
    });

    document.addEventListener('click', function (event) {
        if (!state) return;
        var option = event.target.closest('.suggestions [role=option]');
        if (option && option.parentNode === state.list) {
            choose(Array.prototype.indexOf.call(state.list.children, option));
        }
    });

    // The field was submitted (quick add clears it): close the list.
    document.body.addEventListener('htmx:beforeRequest', function (event) {
        if (state && event.detail.elt === state.input.form) close();
    });
})();
