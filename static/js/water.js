// Water-like floating blobs
const canvas = document.getElementById("bg-canvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

class Blob {
    constructor() {
        this.reset();
    }
    reset() {
        this.x = Math.random()*canvas.width;
        this.y = Math.random()*canvas.height;
        this.radius = Math.random()*50+30;
        this.dx = (Math.random()-0.5)*0.2;
        this.dy = (Math.random()-0.5)*0.2;
        this.color = `rgba(0,191,255,0.2)`; // soft water blue
    }
    draw() {
        const gradient = ctx.createRadialGradient(this.x,this.y,0,this.x,this.y,this.radius);
        gradient.addColorStop(0,this.color);
        gradient.addColorStop(1,'rgba(0,191,255,0)');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x,this.y,this.radius,0,Math.PI*2);
        ctx.fill();
    }
    update() {
        this.x += this.dx;
        this.y += this.dy;
        if(this.x - this.radius > canvas.width) this.x = -this.radius;
        if(this.x + this.radius < 0) this.x = canvas.width + this.radius;
        if(this.y - this.radius > canvas.height) this.y = -this.radius;
        if(this.y + this.radius < 0) this.y = canvas.height + this.radius;
        this.draw();
    }
}

const blobs = [];
for(let i=0;i<30;i++) blobs.push(new Blob());

function animate(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    blobs.forEach(blob=>blob.update());
    requestAnimationFrame(animate);
}
animate();

window.addEventListener("resize",()=>{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
