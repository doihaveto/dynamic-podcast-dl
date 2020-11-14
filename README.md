# dynamic-podcast-dl
Adds audio files from various sources to a podcast RSS feed

Bookmarklet
==
```js
javascript:(function(){div=document.createElement('div');div.style='position:fixed;bottom:0;left:0;width:300px;height:300px;color:#000;font-size:10px;background:#fff;border-right:1px solid #000;border-top:1px solid #000;overflow-y:scroll;white-space:pre;z-index: 1000;';document.body.appendChild(div);fetch('https://example.com/download?'+new URLSearchParams({url:window.location.href,feed:'main',key:'ACCESS_KEY'}),{method:'GET'}).then(r=>{f=r.body.getReader();f.read().then(function p({done,value}){if(!done){div.innerHTML+=new TextDecoder('utf-8').decode(value);div.scrollTop=div.scrollHeight;return f.read().then(p);}else{div.style.background=div.innerHTML.search('. done')>0?'#a7ff91':'#e29494';}})})})();
```
