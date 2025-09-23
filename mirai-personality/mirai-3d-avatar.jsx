/**
 * Mirai 3D Avatar Component
 * Трехмерный аватар с эмоциональными анимациями
 */

const Mirai3DAvatar = () => {
    const mountRef = React.useRef(null);
    const sceneRef = React.useRef(null);
    const rendererRef = React.useRef(null);
    const cameraRef = React.useRef(null);
    const avatarRef = React.useRef(null);
    const [isLoaded, setIsLoaded] = React.useState(false);
    const [currentEmotion, setCurrentEmotion] = React.useState('neutral');
    const [isAnimating, setIsAnimating] = React.useState(false);

    // Инициализация Three.js сцены
    React.useEffect(() => {
        if (!mountRef.current) return;

        // Создание сцены
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a2e);
        sceneRef.current = scene;

        // Создание камеры
        const camera = new THREE.PerspectiveCamera(
            50,
            mountRef.current.clientWidth / mountRef.current.clientHeight,
            0.1,
            1000
        );
        camera.position.z = 3;
        camera.position.y = 0.5;
        cameraRef.current = camera;

        // Создание рендерера
        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.outputEncoding = THREE.sRGBEncoding;
        rendererRef.current = renderer;

        mountRef.current.appendChild(renderer.domElement);

        // Добавление освещения
        setupLighting(scene);

        // Создание аватара
        createAvatar(scene);

        // Обработка изменения размера
        const handleResize = () => {
            if (!mountRef.current) return;
            
            const width = mountRef.current.clientWidth;
            const height = mountRef.current.clientHeight;
            
            camera.aspect = width / height;
            camera.updateProjectionMatrix();
            renderer.setSize(width, height);
        };

        window.addEventListener('resize', handleResize);

        // Анимационный цикл
        const animate = () => {
            requestAnimationFrame(animate);
            
            // Легкое покачивание
            if (avatarRef.current) {
                avatarRef.current.rotation.y += 0.005;
                avatarRef.current.position.y = Math.sin(Date.now() * 0.001) * 0.1;
            }
            
            renderer.render(scene, camera);
        };
        animate();

        setIsLoaded(true);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (mountRef.current && renderer.domElement) {
                mountRef.current.removeChild(renderer.domElement);
            }
            renderer.dispose();
        };
    }, []);

    // Настройка освещения
    const setupLighting = (scene) => {
        // Основной свет
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);

        // Направленный свет
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(5, 5, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        scene.add(directionalLight);

        // Цветной акцентный свет
        const pointLight1 = new THREE.PointLight(0xff6b9d, 0.5, 10);
        pointLight1.position.set(-3, 2, 2);
        scene.add(pointLight1);

        const pointLight2 = new THREE.PointLight(0x667eea, 0.5, 10);
        pointLight2.position.set(3, 2, 2);
        scene.add(pointLight2);
    };

    // Создание 3D аватара
    const createAvatar = (scene) => {
        const avatarGroup = new THREE.Group();
        avatarRef.current = avatarGroup;

        // Голова (основная сфера)
        const headGeometry = new THREE.SphereGeometry(0.8, 32, 32);
        const headMaterial = new THREE.MeshPhongMaterial({
            color: 0xffdbac,
            shininess: 30
        });
        const head = new THREE.Mesh(headGeometry, headMaterial);
        head.castShadow = true;
        head.receiveShadow = true;
        avatarGroup.add(head);

        // Глаза
        const eyeGeometry = new THREE.SphereGeometry(0.15, 16, 16);
        const eyeMaterial = new THREE.MeshPhongMaterial({ color: 0x333333 });
        
        const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        leftEye.position.set(-0.25, 0.2, 0.6);
        avatarGroup.add(leftEye);

        const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
        rightEye.position.set(0.25, 0.2, 0.6);
        avatarGroup.add(rightEye);

        // Блики в глазах
        const highlightGeometry = new THREE.SphereGeometry(0.05, 8, 8);
        const highlightMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff });
        
        const leftHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
        leftHighlight.position.set(-0.2, 0.25, 0.65);
        avatarGroup.add(leftHighlight);

        const rightHighlight = new THREE.Mesh(highlightGeometry, highlightMaterial);
        rightHighlight.position.set(0.3, 0.25, 0.65);
        avatarGroup.add(rightHighlight);

        // Рот (меняется с эмоциями)
        const mouthGeometry = new THREE.CylinderGeometry(0.1, 0.1, 0.05, 8);
        const mouthMaterial = new THREE.MeshPhongMaterial({ color: 0xff4444 });
        const mouth = new THREE.Mesh(mouthGeometry, mouthMaterial);
        mouth.position.set(0, -0.2, 0.6);
        mouth.rotation.x = Math.PI / 2;
        mouth.name = 'mouth';
        avatarGroup.add(mouth);

        // Волосы (стилизованные)
        const hairGeometry = new THREE.SphereGeometry(0.9, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.6);
        const hairMaterial = new THREE.MeshPhongMaterial({
            color: 0x8b4513,
            transparent: true,
            opacity: 0.8
        });
        const hair = new THREE.Mesh(hairGeometry, hairMaterial);
        hair.position.y = 0.3;
        avatarGroup.add(hair);

        // Аксессуары (бантик)
        const bowGeometry = new THREE.BoxGeometry(0.4, 0.2, 0.1);
        const bowMaterial = new THREE.MeshPhongMaterial({ color: 0xff6b9d });
        const bow = new THREE.Mesh(bowGeometry, bowMaterial);
        bow.position.set(0.5, 0.6, 0.3);
        bow.rotation.z = Math.PI / 4;
        avatarGroup.add(bow);

        // Тело (простая капсула)
        const bodyGeometry = new THREE.CapsuleGeometry(0.5, 1.2, 4, 8);
        const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0x4ecdc4 });
        const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
        body.position.y = -1.5;
        body.castShadow = true;
        avatarGroup.add(body);

        // Добавляем к сцене
        scene.add(avatarGroup);

        // Сохраняем ссылки на части для анимаций
        avatarGroup.userData = {
            head,
            leftEye,
            rightEye,
            mouth,
            body
        };
    };

    // Анимации эмоций
    const playEmotionAnimation = (emotion) => {
        if (!avatarRef.current || isAnimating) return;
        
        setIsAnimating(true);
        setCurrentEmotion(emotion);

        const parts = avatarRef.current.userData;
        if (!parts) return;

        // Сброс к нейтральному состоянию
        const resetAnimation = () => {
            parts.head.scale.set(1, 1, 1);
            parts.leftEye.scale.set(1, 1, 1);
            parts.rightEye.scale.set(1, 1, 1);
            parts.mouth.scale.set(1, 1, 1);
            parts.body.rotation.z = 0;
        };

        resetAnimation();

        // Анимации по эмоциям
        switch (emotion) {
            case 'happy':
                // Увеличиваем глаза и рот
                parts.leftEye.scale.setY(0.7);
                parts.rightEye.scale.setY(0.7);
                parts.mouth.scale.setX(1.5);
                parts.head.rotation.z = Math.sin(Date.now() * 0.01) * 0.1;
                break;
                
            case 'excited':
                // Прыгучие движения
                const jumpAnimation = () => {
                    parts.body.position.y = -1.5 + Math.sin(Date.now() * 0.02) * 0.2;
                    parts.head.scale.setY(1 + Math.sin(Date.now() * 0.02) * 0.1);
                };
                jumpAnimation();
                break;
                
            case 'curious':
                // Наклон головы
                parts.head.rotation.z = 0.3;
                parts.leftEye.scale.setY(1.2);
                parts.rightEye.scale.setY(1.2);
                break;
                
            case 'surprised':
                // Широко открытые глаза
                parts.leftEye.scale.set(1.5, 1.5, 1.5);
                parts.rightEye.scale.set(1.5, 1.5, 1.5);
                parts.mouth.scale.setY(1.5);
                break;
                
            case 'thoughtful':
                // Медленные кивки
                const thinkAnimation = () => {
                    parts.head.rotation.x = Math.sin(Date.now() * 0.005) * 0.2;
                };
                thinkAnimation();
                break;
                
            default:
                // Нейтральное состояние
                break;
        }

        // Завершение анимации
        setTimeout(() => {
            setIsAnimating(false);
        }, 2000);
    };

    // Эмоциональные кнопки
    const emotions = [
        { name: 'happy', label: 'Счастливая', emoji: '😊', color: '#ffd93d' },
        { name: 'excited', label: 'Возбужденная', emoji: '✨', color: '#ff6b9d' },
        { name: 'curious', label: 'Любопытная', emoji: '🤔', color: '#4ecdc4' },
        { name: 'surprised', label: 'Удивленная', emoji: '😲', color: '#ff8c42' },
        { name: 'thoughtful', label: 'Задумчивая', emoji: '💭', color: '#667eea' }
    ];

    return (
        <div className="avatar-container">
            <div className="avatar-viewer" ref={mountRef}>
                {!isLoaded && (
                    <div className="loading-avatar">
                        <div className="spinner"></div>
                        <p>Загружаю 3D аватар...</p>
                    </div>
                )}
            </div>
            
            <div className="emotion-controls">
                <h3>Эмоции Mirai-chan</h3>
                <div className="emotion-buttons">
                    {emotions.map((emotion) => (
                        <button
                            key={emotion.name}
                            onClick={() => playEmotionAnimation(emotion.name)}
                            disabled={isAnimating}
                            className={`emotion-btn ${currentEmotion === emotion.name ? 'active' : ''}`}
                            style={{ '--emotion-color': emotion.color }}
                        >
                            <span className="emotion-emoji">{emotion.emoji}</span>
                            <span className="emotion-label">{emotion.label}</span>
                        </button>
                    ))}
                </div>
                
                <div className="avatar-info">
                    <p>🎭 Текущая эмоция: <strong>{currentEmotion}</strong></p>
                    <p>✨ Кликайте на эмоции чтобы увидеть анимации!</p>
                </div>
            </div>

            <style jsx>{`
                .avatar-container {
                    display: flex;
                    flex-direction: column;
                    height: 100vh;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    overflow: hidden;
                }

                .avatar-viewer {
                    flex: 1;
                    position: relative;
                    min-height: 400px;
                }

                .loading-avatar {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    text-align: center;
                    color: #ffd93d;
                }

                .spinner {
                    width: 50px;
                    height: 50px;
                    border: 4px solid rgba(255, 217, 61, 0.3);
                    border-top: 4px solid #ffd93d;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 20px;
                }

                .emotion-controls {
                    background: rgba(0,0,0,0.3);
                    backdrop-filter: blur(10px);
                    padding: 30px;
                    border-radius: 20px 20px 0 0;
                    margin-top: auto;
                }

                .emotion-controls h3 {
                    text-align: center;
                    margin-bottom: 20px;
                    background: linear-gradient(45deg, #ffd93d, #ff6b9d);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    font-size: 1.5em;
                }

                .emotion-buttons {
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    flex-wrap: wrap;
                    margin-bottom: 20px;
                }

                .emotion-btn {
                    background: rgba(255,255,255,0.1);
                    border: 2px solid var(--emotion-color);
                    border-radius: 15px;
                    padding: 15px 20px;
                    color: white;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 8px;
                    min-width: 90px;
                    position: relative;
                    overflow: hidden;
                }

                .emotion-btn:hover:not(:disabled) {
                    background: var(--emotion-color);
                    transform: translateY(-3px);
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                }

                .emotion-btn:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .emotion-btn.active {
                    background: var(--emotion-color);
                    box-shadow: 0 0 20px var(--emotion-color);
                }

                .emotion-emoji {
                    font-size: 1.8em;
                    animation: bounce 2s infinite;
                }

                .emotion-label {
                    font-size: 0.85em;
                    font-weight: 500;
                    text-align: center;
                }

                .avatar-info {
                    text-align: center;
                    opacity: 0.8;
                    font-size: 0.9em;
                    line-height: 1.6;
                }

                .avatar-info p {
                    margin: 5px 0;
                }

                .avatar-info strong {
                    color: #ffd93d;
                    text-transform: capitalize;
                }

                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }

                @keyframes bounce {
                    0%, 20%, 50%, 80%, 100% {
                        transform: translateY(0);
                    }
                    40% {
                        transform: translateY(-5px);
                    }
                    60% {
                        transform: translateY(-3px);
                    }
                }

                @media (max-width: 768px) {
                    .emotion-buttons {
                        gap: 10px;
                    }
                    
                    .emotion-btn {
                        min-width: 70px;
                        padding: 12px 15px;
                    }
                    
                    .emotion-emoji {
                        font-size: 1.5em;
                    }
                    
                    .emotion-label {
                        font-size: 0.75em;
                    }
                }
            `}</style>
        </div>
    );
};

// Экспортируем компонент
window.Mirai3DAvatar = Mirai3DAvatar;