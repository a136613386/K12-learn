CREATE TABLE IF NOT EXISTS knowledge_points (
    id INT PRIMARY KEY,
    parent_id INT NULL,
    name VARCHAR(100) NOT NULL,
    level TINYINT NOT NULL DEFAULT 1,
    importance TINYINT NOT NULL,
    difficulty TINYINT NOT NULL,
    core_requirement TEXT NOT NULL,
    sort_order INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_knowledge_points_sort_order (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS questions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stem TEXT NOT NULL,
    options TEXT NULL,
    answer VARCHAR(255) NULL,
    label_id INT NULL,
    source VARCHAR(255) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_questions_label_id (label_id),
    CONSTRAINT fk_questions_label_id FOREIGN KEY (label_id) REFERENCES knowledge_points(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS prediction_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    text_hash VARCHAR(64) NOT NULL,
    input_text TEXT NOT NULL,
    predicted_label_id INT NOT NULL,
    confidence DECIMAL(8, 6) NOT NULL,
    elapsed_ms DECIMAL(10, 2) NOT NULL,
    cache_hit TINYINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_prediction_logs_text_hash (text_hash),
    INDEX idx_prediction_logs_created_at (created_at),
    INDEX idx_prediction_logs_predicted_label_id (predicted_label_id),
    CONSTRAINT fk_prediction_logs_label_id FOREIGN KEY (predicted_label_id) REFERENCES knowledge_points(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO knowledge_points
    (id, parent_id, name, level, importance, difficulty, core_requirement, sort_order)
VALUES
    (0, NULL, '孟德尔遗传定律', 1, 5, 4, '会判断显隐性、分离比、基因型和表现型', 1),
    (1, NULL, '减数分裂与受精作用', 1, 5, 5, '会分析染色体、DNA、染色单体数量变化', 2),
    (2, NULL, '伴性遗传', 1, 5, 4, '会分析红绿色盲、抗维生素D佝偻病等遗传图解', 3),
    (3, NULL, 'DNA是主要遗传物质', 1, 5, 3, '掌握肺炎链球菌转化实验、噬菌体侵染细菌实验', 4),
    (4, NULL, 'DNA结构与复制', 1, 5, 4, '掌握双螺旋、碱基互补配对、半保留复制', 5),
    (5, NULL, '基因指导蛋白质合成', 1, 5, 5, '掌握转录、翻译、密码子、氨基酸关系', 6),
    (6, NULL, '基因表达与性状关系', 1, 4, 4, '理解基因、蛋白质、性状之间的关系', 7),
    (7, NULL, '基因突变和基因重组', 1, 4, 4, '区分突变、重组及其在变异中的意义', 8),
    (8, NULL, '染色体变异', 1, 4, 4, '掌握结构变异、数目变异、染色体组', 9),
    (9, NULL, '人类遗传病', 1, 4, 3, '会区分单基因、多基因、染色体异常遗传病', 10),
    (10, NULL, '基因在染色体上', 1, 4, 3, '理解萨顿假说、摩尔根果蝇实验', 11),
    (11, NULL, '现代生物进化理论', 1, 4, 4, '掌握自然选择、基因频率、物种形成', 12),
    (12, NULL, '生物共同祖先证据', 1, 3, 2, '掌握化石、比较解剖学、胚胎学等证据', 13),
    (13, NULL, '协同进化与生物多样性', 1, 3, 3, '理解共同进化和生物多样性的形成', 14),
    (14, NULL, '探究实践与模型实验', 1, 3, 3, '会解释模拟实验、观察实验和调查实验目的', 15)
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    importance = VALUES(importance),
    difficulty = VALUES(difficulty),
    core_requirement = VALUES(core_requirement),
    sort_order = VALUES(sort_order);
