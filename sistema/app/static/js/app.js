// Pequenos ajustes de uso do sistema (sem depender de nenhuma outra biblioteca além do Bootstrap).
(function () {
  "use strict";

  // 1) Mensagens de sucesso somem sozinhas depois de alguns segundos.
  //    Mensagens de erro continuam na tela até serem fechadas.
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".alert-success").forEach(function (alerta) {
      setTimeout(function () {
        if (window.bootstrap && document.body.contains(alerta)) {
          window.bootstrap.Alert.getOrCreateInstance(alerta).close();
        }
      }, 6000);
    });
  });

  // 2) Evita registro duplicado por clique duplo: depois do envio de um formulário,
  //    os botões dele ficam desativados. Se o usuário cancelar a confirmação
  //    ("Tem certeza?"), o envio é cancelado e os botões continuam ativos.
  document.addEventListener("submit", function (evento) {
    if (evento.defaultPrevented) { return; }
    var form = evento.target;
    if (!form.method || form.method.toLowerCase() !== "post") { return; }
    setTimeout(function () {
      form.querySelectorAll("button[type=submit]").forEach(function (botao) { botao.disabled = true; });
    }, 0);
  });

  // 3) Ao voltar pelo botão "voltar" do navegador, os botões voltam a funcionar.
  window.addEventListener("pageshow", function (evento) {
    if (evento.persisted) {
      document.querySelectorAll("button[type=submit]").forEach(function (botao) { botao.disabled = false; });
    }
  });
})();
