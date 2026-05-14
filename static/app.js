'use strict';

document.addEventListener('DOMContentLoaded', () => {

  // ── Éléments DOM ──────────────────────────────────────────────────────────
  const form          = document.getElementById('query-form');
  const submitBtn     = document.getElementById('submit-btn');
  const resultsSection = document.getElementById('results');
  const errorBox      = document.getElementById('error-box');
  const resultCard    = document.getElementById('result-card');
  const resultQuestion = document.getElementById('result-question');
  const answerBlock   = document.getElementById('answer-block');
  const resultAnswer  = document.getElementById('result-answer');
  const sourcesList   = document.getElementById('sources-list');

  // ── Soumission du formulaire ───────────────────────────────────────────────
  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question     = document.getElementById('question').value.trim();
    const topK         = parseInt(document.getElementById('top-k').value, 10) || 2;
    const retrieveOnly = document.getElementById('retrieve-only').checked;

    if (!question) {
      showError('Veuillez saisir une question avant de lancer la recherche.');
      return;
    }

    setLoading(true);
    hide(resultsSection);

    try {
      const res  = await fetch('/query', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ question, top_k: topK, retrieve_only: retrieveOnly }),
      });

      const data = await res.json();

      if (!res.ok) {
        showError(data.error || 'Erreur serveur.', data.hint || null);
        return;
      }

      renderResults(data);

    } catch (_) {
      showError(
        'Impossible de contacter l\'API.',
        'Vérifiez que app.py est lancé sur http://localhost:5000.'
      );
    } finally {
      setLoading(false);
    }
  });

  // ── Rendu des résultats ────────────────────────────────────────────────────
  function renderResults(data) {
    // Question
    resultQuestion.textContent = data.question;

    // Réponse (facultative)
    if (data.answer) {
      resultAnswer.textContent = data.answer;
      show(answerBlock);
    } else {
      hide(answerBlock);
    }

    // Sources
    sourcesList.innerHTML = '';
    if (data.sources && data.sources.length > 0) {
      data.sources.forEach((src) => {
        const li = document.createElement('li');
        li.className = 'source-item';
        li.innerHTML =
          `<div class="source-header">
             <span class="source-name">${esc(src.source)}</span>
             <span class="source-score">score : ${src.score}</span>
           </div>
           <p class="source-excerpt">${esc(src.excerpt)}…</p>`;
        sourcesList.appendChild(li);
      });
    } else {
      sourcesList.innerHTML = '<li class="no-sources">Aucune source retrouvée.</li>';
    }

    hide(errorBox);
    show(resultCard);
    show(resultsSection);
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ── Affichage des erreurs ──────────────────────────────────────────────────
  function showError(message, hint) {
    errorBox.innerHTML = `<strong>Erreur :</strong> ${esc(message)}` +
      (hint ? `<small>${esc(hint)}</small>` : '');
    hide(resultCard);
    show(errorBox);
    show(resultsSection);
    errorBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ── État chargement ────────────────────────────────────────────────────────
  function setLoading(loading) {
    submitBtn.disabled    = loading;
    submitBtn.textContent = loading ? 'Recherche en cours…' : 'Rechercher';
  }

  // ── Utilitaires ────────────────────────────────────────────────────────────
  function show(el) { el.classList.remove('hidden'); }
  function hide(el) { el.classList.add('hidden'); }

  function esc(str) {
    const d = document.createElement('div');
    d.appendChild(document.createTextNode(String(str)));
    return d.innerHTML;
  }

});
