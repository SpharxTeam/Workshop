{
  "description": "物理材料属性定义",
  "version": "1.0.0",
  "materials": {
    "default": {
      "density": 1000.0,
      "friction": 0.5,
      "restitution": 0.3,
      "description": "默认材料属性"
    },
    "wood": {
      "density": 650.0,
      "friction": 0.4,
      "restitution": 0.3,
      "description": "木材 - 中等密度，中等摩擦"
    },
    "metal": {
      "density": 7850.0,
      "friction": 0.15,
      "restitution": 0.1,
      "description": "金属 - 高密度，低摩擦，低弹性"
    },
    "plastic": {
      "density": 950.0,
      "friction": 0.3,
      "restitution": 0.5,
      "description": "塑料 - 低密度，中等摩擦，高弹性"
    },
    "rubber": {
      "density": 1100.0,
      "friction": 0.8,
      "restitution": 0.7,
      "description": "橡胶 - 中等密度，高摩擦，高弹性"
    },
    "concrete": {
      "density": 2400.0,
      "friction": 0.6,
      "restitution": 0.05,
      "description": "混凝土 - 高密度，中等摩擦，低弹性"
    },
    "glass": {
      "density": 2500.0,
      "friction": 0.1,
      "restitution": 0.8,
      "description": "玻璃 - 高密度，低摩擦，高弹性"
    },
    "fabric": {
      "density": 300.0,
      "friction": 0.4,
      "restitution": 0.2,
      "description": "织物 - 低密度，中等摩擦，低弹性"
    }
  },
  "categories": {
    "structural": ["concrete", "metal", "wood"],
    "decorative": ["plastic", "glass", "fabric"],
    "functional": ["rubber", "default"]
  },
  "simulation_presets": {
    "default": {
      "gravity": -9.81,
      "time_scale": 1.0,
      "substeps": 10,
      "solver_iterations": 50
    },
    "slow_motion": {
      "gravity": -9.81,
      "time_scale": 0.5,
      "substeps": 20,
      "solver_iterations": 100
    },
    "fast_simulation": {
      "gravity": -9.81,
      "time_scale": 2.0,
      "substeps": 5,
      "solver_iterations": 25
    }
  }
}
