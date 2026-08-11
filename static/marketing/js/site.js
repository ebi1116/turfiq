const responsiveStyles=document.createElement("link"),siteScript=document.currentScript;responsiveStyles.rel="stylesheet";responsiveStyles.href=new URL("../css/responsive.css?v=1",siteScript.src).href;document.head.appendChild(responsiveStyles);
document.addEventListener("DOMContentLoaded",()=>{
  let favicon=document.querySelector("link[rel~='icon']");
  if(!favicon){favicon=document.createElement("link");favicon.rel="icon";favicon.type="image/png";document.head.appendChild(favicon)}
  favicon.href="/static/images/turfiq-favicon-v1.png";
  const reducedMotion=matchMedia("(prefers-reduced-motion: reduce)").matches;
  const splash=document.getElementById("cinematicSplash");
  const splashKey="turfiq-simple-image-intro-v2";
  const shouldPlaySplash=Boolean(splash&&window.gsap&&!reducedMotion&&!sessionStorage.getItem(splashKey));
  if(splash&&!shouldPlaySplash)splash.remove();
  if(shouldPlaySplash){
    sessionStorage.setItem(splashKey,"1");
    document.body.style.overflow="hidden";
    splash.classList.add("is-playing");
    const sq=gsap.utils.selector(splash);
    gsap.set(splash,{autoAlpha:0,scale:1.04});
    gsap.set(sq(".source-ground-crop"),{autoAlpha:0,x:-90,scale:.94});
    gsap.set(sq(".simple-splash-copy strong"),{autoAlpha:0,y:24,filter:"blur(10px)"});
    gsap.set(sq(".simple-analytics b"),{autoAlpha:0,y:16,letterSpacing:".75em"});
    gsap.set(sq(".simple-analytics i"),{scaleX:0});
    gsap.set(sq(".simple-splash-copy p"),{autoAlpha:0,y:14});
    const intro=gsap.timeline({defaults:{ease:"power3.out"}});
    intro.to(splash,{autoAlpha:1,scale:1,duration:.4},0)
      .to(sq(".source-ground-crop"),{autoAlpha:1,x:0,scale:1,duration:.65,ease:"back.out(1.15)"},.4)
      .to(sq(".simple-splash-copy strong"),{autoAlpha:1,y:0,filter:"blur(0px)",duration:.45},1.1)
      .to(sq(".simple-analytics b"),{autoAlpha:1,y:0,letterSpacing:".42em",duration:.45},1.65)
      .to(sq(".simple-analytics i"),{scaleX:1,duration:.4,stagger:.05},1.7)
      .to(sq(".simple-splash-copy p"),{autoAlpha:1,y:0,duration:.42},2.2)
      .to(sq(".simple-splash-lockup"),{scale:1.02,duration:.2,yoyo:true,repeat:1},2.85)
      .to(splash,{autoAlpha:0,duration:.45,ease:"power2.inOut",onComplete:()=>{splash.classList.add("is-finished");splash.remove();document.body.style.overflow=""}},3.35);
  }
  document.querySelectorAll(".marketing-nav .m-brand,.site-footer .m-brand").forEach((brand,index)=>{
    brand.style.width=index?"148px":"68px";
    brand.style.height=index?"148px":"68px";
    brand.style.flexBasis=index?"auto":"68px";
    brand.style.borderRadius="24%";
    brand.style.fontSize="0";
    brand.style.background="url('/static/images/turfiq-profile-logo-v2.png') center/contain no-repeat";
    Array.from(brand.children).forEach(child=>child.style.display="none");
  });
  const lockup=document.getElementById("analyticsLockup");
  if(lockup){
    lockup.classList.add("hero-cover-lockup");
    lockup.innerHTML='<img class="hero-cover-image" src="/static/images/turfiq-cover-pic.png" alt="TurfIQ Analytics — Smarter turf, higher profit"><span class="hero-ball-mask" aria-hidden="true"></span><span class="hero-moving-ball" aria-hidden="true"><i></i><b></b><em></em></span>';
  }
  if(lockup&&window.gsap&&!reducedMotion&&!lockup.classList.contains("hero-cover-lockup")){
    const q=gsap.utils.selector(lockup);
    gsap.set(lockup,{autoAlpha:0,scale:1.05});
    gsap.set(q(".chart-bars rect"),{autoAlpha:0,scaleY:0,transformOrigin:"center bottom"});
    gsap.set(q(".analytics-ring path"),{autoAlpha:0,strokeDasharray:600,strokeDashoffset:600});
    gsap.set(q(".trend-path,.arrow-head,.trend-line circle"),{autoAlpha:0});
    gsap.set(q(".trend-path"),{strokeDasharray:1,strokeDashoffset:1});
    gsap.set(q(".brand-letters span"),{autoAlpha:0,y:28,filter:"blur(10px)"});
    gsap.set(q(".brand-letters i"),{autoAlpha:0,scaleY:0});
    gsap.set(q(".analytics-word span"),{autoAlpha:0});
    gsap.set(q(".analytics-word"),{letterSpacing:".75em"});
    gsap.set(q(".analytics-word b"),{scaleX:0});
    gsap.set(q(".lockup-tagline span,.lockup-tagline i"),{autoAlpha:0,y:14});
    const tl=gsap.timeline({delay:shouldPlaySplash?3.85:0,defaults:{ease:"power3.out"}});
    tl.to(lockup,{autoAlpha:1,scale:1,duration:.5},0)
      .from(".premium-hero",{autoAlpha:0,scale:1.02,duration:.5,transformOrigin:"center"},0)
      .to(q(".analytics-ring path"),{autoAlpha:1,strokeDashoffset:0,duration:.55,stagger:.07},.5)
      .to(q(".chart-bars rect"),{autoAlpha:1,scaleY:1,duration:.32,stagger:.07,ease:"back.out(1.3)"},.5)
      .to(q(".trend-path"),{autoAlpha:1,strokeDashoffset:0,duration:.48,ease:"power2.inOut"},.62)
      .to(q(".trend-line circle"),{autoAlpha:1,duration:.18,stagger:.07},.72)
      .to(q(".arrow-head"),{autoAlpha:1,duration:.22},.92)
      .fromTo(q(".trend-line"),{filter:"url(#softGlow) brightness(1)"},{filter:"url(#softGlow) brightness(1.35)",duration:.18,yoyo:true,repeat:1},.94)
      .to(q(".lockup-symbol"),{scale:1.04,duration:.14,ease:"power2.out",yoyo:true,repeat:1,transformOrigin:"center"},1.1)
      .to(q(".brand-letters span"),{autoAlpha:1,y:0,filter:"blur(0px)",duration:.28,stagger:.05},1.35)
      .to(q(".brand-letters i"),{autoAlpha:1,scaleY:1,duration:.3},1.53)
      .to(q(".analytics-word span"),{autoAlpha:1,duration:.38,stagger:.035},1.95)
      .to(q(".analytics-word"),{letterSpacing:".34em",duration:.6,ease:"power3.inOut"},1.95)
      .to(q(".analytics-word b"),{scaleX:1,duration:.6,ease:"power3.inOut"},1.95)
      .to(q(".lockup-tagline span"),{autoAlpha:1,y:0,duration:.38,stagger:.12},2.55)
      .to(q(".lockup-tagline i"),{autoAlpha:1,y:0,scale:1,duration:.2,stagger:.12,ease:"back.out(2)"},2.7)
      .to(lockup,{scale:1.02,duration:.2,ease:"power2.out",yoyo:true,repeat:1},3.15);
    lockup.addEventListener("mouseenter",()=>{
      gsap.to(q(".trend-line"),{filter:"url(#softGlow) brightness(1.4)",duration:.3,overwrite:"auto"});
    });
    lockup.addEventListener("mouseleave",()=>{
      gsap.to(q(".trend-line"),{filter:"url(#softGlow) brightness(1)",duration:.3,overwrite:"auto"});
    });
  }
  const root=document.documentElement,theme=localStorage.getItem("turfiq-marketing-theme")||"light";
  root.dataset.theme=theme;
  document.getElementById("marketingTheme")?.addEventListener("click",()=>{const next=root.dataset.theme==="dark"?"light":"dark";root.dataset.theme=next;localStorage.setItem("turfiq-marketing-theme",next)});
  const nav=document.querySelector(".marketing-nav");
  const updateNav=()=>nav?.classList.toggle("scrolled",scrollY>20);
  updateNav();
  addEventListener("scroll",updateNav,{passive:true});
  if(window.AOS)AOS.init({duration:650,once:true,offset:30});
  document.querySelectorAll("img").forEach(img=>{if(!img.loading&&!img.closest(".brand-splash"))img.loading="lazy"});
});
