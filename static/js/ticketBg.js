const canvas = document.getElementById("ticket-bg-canvas");
const ctx = canvas.getContext("2d");
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const icons = ["🎫", "💬", "🔔"];

class TicketIcon {
    constructor() {
        this.reset();
    }
    reset() {
        this.x = Math.random() * canvas.width;
        this.y = canvas.height + Math.random() * 100;
        this.size = Math.random() * 40 + 30;
        this.speed = Math.random() * 0.5 + 0.2;
        this.angle = Math.random() * 2 * Math.PI;
        this.angleSpeed = (Math.random()-0.5)*0.01;
        this.waveOffset = Math.random() * 1000;
        this.icon = icons[Math.floor(Math.random() * icons.length)];
        this.opacity = Math.random() * 0.5 + 0.5;
        this.color = `hsl(${Math.random()*360}, 80%, 70%)`;
    }
    draw() {
        ctx.save();
        ctx.font = `${this.size}px Arial`;
        ctx.translate(this.x + Math.sin(this.waveOffset + this.y/50)*10, this.y);
        ctx.rotate(this.angle);
        ctx.globalAlpha = this.opacity;
        ctx.shadowColor = this.color;
        ctx.shadowBlur = 15;
        ctx.fillStyle = this.color;
        ctx.fillText(this.icon, -this.size/2, this.size/2);
        ctx.restore();
        ctx.globalAlpha = 1;
    }
    update() {
        this.y -= this.speed;
        this.angle += this.angleSpeed;
        if (this.y < -50) this.reset();
        this.draw();
    }
}

const ticketIcons = [];
for (let i=0;i<50;i++) ticketIcons.push(new TicketIcon());

function animate() {
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ticketIcons.forEach(icon=>icon.update());
    requestAnimationFrame(animate);
}

animate();

window.addEventListener("resize", ()=>{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});
