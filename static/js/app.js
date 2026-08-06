document.addEventListener("DOMContentLoaded",()=>{
  document.querySelectorAll(".google-auth-button").forEach(button=>button.addEventListener("pointerdown",event=>{
    const ripple=button.querySelector(".google-ripple"),rect=button.getBoundingClientRect();
    ripple.style.left=`${event.clientX-rect.left-10}px`;ripple.style.top=`${event.clientY-rect.top-10}px`;
    button.classList.remove("is-rippling");void button.offsetWidth;button.classList.add("is-rippling");
  }));
  const root=document.documentElement, saved=localStorage.getItem("turfiq-theme");
  if(saved) root.dataset.bsTheme=saved;
  document.getElementById("themeToggle")?.addEventListener("click",()=>{const next=root.dataset.bsTheme==="dark"?"light":"dark";root.dataset.bsTheme=next;localStorage.setItem("turfiq-theme",next);});
  document.getElementById("menuToggle")?.addEventListener("click",()=>document.getElementById("sidebar")?.classList.toggle("open"));
  document.querySelectorAll(".counter").forEach(el=>{const target=parseFloat(el.dataset.value)||0,start=performance.now();const tick=now=>{const p=Math.min((now-start)/650,1);el.textContent=Math.round(target*(1-Math.pow(1-p,3))).toLocaleString();if(p<1)requestAnimationFrame(tick)};requestAnimationFrame(tick)});
  document.querySelectorAll(".progress-bar[data-width]").forEach(el=>requestAnimationFrame(()=>el.style.width=`${el.dataset.width}%`));
  document.querySelectorAll(".goal-ring").forEach(el=>el.style.setProperty("--progress",el.dataset.progress));
  if(window.AOS) AOS.init({duration:500,once:true,offset:20});
  const raw=document.getElementById("chart-data"); if(!raw||!window.Chart)return; const data=JSON.parse(raw.textContent);
  Chart.defaults.font.family="DM Sans"; Chart.defaults.color="#85938d"; Chart.defaults.borderColor="rgba(130,150,141,.14)";
  const gradient=(ctx)=>{const g=ctx.createLinearGradient(0,0,0,300);g.addColorStop(0,"rgba(13,187,117,.28)");g.addColorStop(1,"rgba(13,187,117,0)");return g};
  const base={responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{grid:{display:false},ticks:{font:{size:10}}},y:{beginAtZero:true,ticks:{font:{size:10}}}}};
  const revenue=document.getElementById("revenueChart"); if(revenue)new Chart(revenue,{type:"line",data:{labels:data.daily.labels,datasets:[{data:data.daily.values,borderColor:"#0dbb75",backgroundColor:gradient(revenue.getContext("2d")),fill:true,tension:.42,pointRadius:0,borderWidth:2.5}]},options:base});
  const monthly=document.getElementById("monthlyChart"); if(monthly)new Chart(monthly,{type:"bar",data:{labels:data.monthly.labels,datasets:[{data:data.monthly.values,backgroundColor:"#20c986",borderRadius:7,borderSkipped:false}]},options:base});
  const donut=(id,d,colors)=>{const el=document.getElementById(id);if(el)new Chart(el,{type:"doughnut",data:{labels:d.labels,datasets:[{data:d.values,backgroundColor:colors,borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:"68%",plugins:{legend:{position:"bottom",labels:{usePointStyle:true,boxWidth:8,font:{size:10}}}}}})};
  donut("paymentChart",data.payment,["#0dbb75","#4676f2","#ffb84d","#8b6cf0"]);donut("sportsChart",data.sports,["#0dbb75","#4676f2","#ff7d68","#b0bd5c"]);
  const hour=document.getElementById("hourChart");if(hour)new Chart(hour,{type:"bar",data:{labels:data.hours.labels,datasets:[{data:data.hours.values,backgroundColor:data.hours.values.map(v=>v===Math.max(...data.hours.values)?"#0dbb75":"rgba(13,187,117,.18)"),borderRadius:5}]},options:base});
});
