async function loadNews(){
    let res = await fetch('/api/news'), j = await res.json();
    for(let [src, arr] of Object.entries(j)){
      let ul = document.querySelector(`#${src} ul`);
      arr.forEach(a=>{
        let li = document.createElement('li');
        li.innerHTML = `<a href="${a.link}" target="_blank">${a.title}</a> <small>${a.date}</small>`;
        ul.append(li);
      });
    }
  }
  async function loadTranscripts(){
    let res = await fetch('/api/transcripts'), ep = await res.json();
    let ul = document.querySelector('#transcripts ul');
    ep.forEach(e=>{
      let li = document.createElement('li');
      li.innerHTML = `<strong>${e.episode}</strong>: ${e.transcript.substring(0,200)}...`;
      ul.append(li);
    });
  }
  loadNews();
  loadTranscripts(); 