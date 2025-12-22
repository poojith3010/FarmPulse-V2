document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.createElement('canvas');
    document.body.prepend(canvas); // Prepend to be behind other elements
    const ctx = canvas.getContext('2d');

    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.zIndex = '-1';
    canvas.style.background = 'linear-gradient(to bottom right, #000a05, #00180c)';

    let width, height, particles, mouse;

    const PARTICLE_COLOR = '#34d399';
    const PARTICLE_COUNT = 100;
    const CONNECTION_DISTANCE = 120;
    const MOUSE_REPEL_RADIUS = 150;
    const MOUSE_REPEL_STRENGTH = 0.5;

    function init() {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        
        mouse = { x: null, y: null };
        particles = [];

        for (let i = 0; i < PARTICLE_COUNT; i++) {
            particles.push({
                x: Math.random() * width,
                y: Math.random() * height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                radius: Math.random() * 1.5 + 1,
            });
        }
    }

    function animate() {
        ctx.clearRect(0, 0, width, height);
        
        updateParticles();
        drawLines();
        drawParticles();

        requestAnimationFrame(animate);
    }

    function updateParticles() {
        particles.forEach(p => {
            // Movement
            p.x += p.vx;
            p.y += p.vy;

            // Wall collision
            if (p.x < 0 || p.x > width) p.vx *= -1;
            if (p.y < 0 || p.y > height) p.vy *= -1;

            // Mouse interaction
            if (mouse.x !== null && mouse.y !== null) {
                const dx = p.x - mouse.x;
                const dy = p.y - mouse.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < MOUSE_REPEL_RADIUS) {
                    const force = (MOUSE_REPEL_RADIUS - dist) / MOUSE_REPEL_RADIUS;
                    p.x += (dx / dist) * force * MOUSE_REPEL_STRENGTH;
                    p.y += (dy / dist) * force * MOUSE_REPEL_STRENGTH;
                }
            }
        });
    }

    function drawParticles() {
        ctx.fillStyle = PARTICLE_COLOR;
        particles.forEach(p => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            ctx.fill();
        });
    }

    function drawLines() {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const p1 = particles[i];
                const p2 = particles[j];
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < CONNECTION_DISTANCE) {
                    const opacity = 1 - (dist / CONNECTION_DISTANCE);
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(52, 211, 153, ${opacity})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
    }

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
    });

    window.addEventListener('mousemove', (e) => {
        mouse.x = e.x;
        mouse.y = e.y;
    });
    
    window.addEventListener('mouseout', () => {
        mouse.x = null;
        mouse.y = null;
    });

    init();
    animate();
});