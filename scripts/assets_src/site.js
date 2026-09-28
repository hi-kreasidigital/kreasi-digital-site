/* Kreasi Digital v3 -- menu mobile + form newsletter */
(function () {
  var toggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A' && nav.classList.contains('open')) {
        nav.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // Newsletter -> webhook Airtable Automation.
  // Webhook Airtable tidak mendukung CORS, jadi data dikirim sebagai form biasa
  // (URLSearchParams) dengan mode 'no-cors'. Balasan tidak bisa dibaca browser,
  // jadi pesan sukses tampil setelah kiriman berangkat. Cek duplikat & filter bot
  // dilakukan di automation Airtable. Field 'website' adalah jebakan bot.
  var forms = document.querySelectorAll('form[data-nl]');
  Array.prototype.forEach.call(forms, function (form) {
    var cfg;
    try { cfg = JSON.parse(form.getAttribute('data-nl')); } catch (err) { return; }
    var input = form.querySelector('input[type=email]');
    var trap = form.querySelector('input[name=website]');
    var btn = form.querySelector('button');
    var msg = form.querySelector('.nl-msg');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = (input.value || '').trim();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { msg.textContent = cfg.invalid; input.focus(); return; }
      btn.disabled = true;
      msg.textContent = cfg.sending;
      fetch(cfg.url, {
        method: 'POST',
        mode: 'no-cors',
        body: new URLSearchParams({ email: email, sumber_halaman: cfg.source, bahasa: cfg.lang, website: trap ? trap.value : '' })
      }).then(function () {
        msg.textContent = cfg.ok;
        input.value = '';
      }).catch(function () {
        msg.textContent = cfg.err;
      }).then(function () { btn.disabled = false; });
    });
  });
})();
