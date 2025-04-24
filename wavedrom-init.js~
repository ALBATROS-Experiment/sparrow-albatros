// First, load WaveDrom library
(function loadScript(src, callback) {
  const script = document.createElement('script');
  script.src = src;
  script.onload = callback;
  document.head.appendChild(script);
})('https://cdnjs.cloudflare.com/ajax/libs/wavedrom/2.6.8/wavedrom.min.js', function() {
  // After WaveDrom is loaded, load the skin
  (function loadScript(src, callback) {
    const script = document.createElement('script');
    script.src = src;
    script.onload = callback;
    document.head.appendChild(script);
  })('https://cdnjs.cloudflare.com/ajax/libs/wavedrom/2.6.8/skins/default.js', function() {
    // After both are loaded, process the WaveDrom diagrams
    console.log('WaveDrom and skin loaded, processing diagrams...');
    window.addEventListener('load', function() {
      if (typeof WaveDrom !== 'undefined') {
        WaveDrom.ProcessAll();
        console.log('WaveDrom diagrams processed');
      } else {
        console.error('WaveDrom still not loaded properly');
      }
    });
  });
});
