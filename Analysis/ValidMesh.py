import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import vectorized


class ValidMesh:

    def __init__(self):
        self.valid_meshes = []

    def set_polygon(self):
        # --- Your polygon setup ---

        shift_x = -11.65
        shift_y = -4.5
        translation_vector = (shift_x, shift_y)

        def shift_xy(boundary_points, shift_vector):
            return [(x + shift_vector[0], y + shift_vector[1]) for x, y in boundary_points]

        # Pillars as holes
        pillar1 = [(2.69, 5.25), (3.3, 5.25), (3.3, 6.15), (2.69, 6.15)]
        pillar2 = [(5.69, 5.25), (6.3, 5.25), (6.3, 6.15), (5.69, 6.15)]
        pillar3 = [(8.69, 5.25), (8.92, 5.25), (8.92, 6.15), (8.69, 6.15)]
        pillar4 = [(11.31, 5.25), (11.92, 5.25), (11.92, 6.15), (11.31, 6.15)]
        pillar5 = [(14.69, 5.25), (14.92, 5.25), (14.92, 6.15), (14.69, 6.15)]
        pillar6 = [(17.69, 5.25), (18.3, 5.25), (18.3, 6.15), (17.69, 6.15)]
        pillar7 = [(20.69, 5.25), (21.3, 5.25), (21.3, 6.15), (20.69, 6.15)]
        pillar8 = [(17.685, 0), (17.915, 1.05), (17.915, 1.05), (17.685, 0)]
        pillar9 = [(16.74, 0.0), (16.97, 0.0), (16.97, 0.9), (16.74, 0.9)]
        pillars = [pillar1, pillar2, pillar3, pillar4, pillar5, pillar6, pillar7, pillar8, pillar9]

        holes = [shift_xy(p, translation_vector) for p in pillars]

        # Main Room
        A = (0, 1.25)
        B = (2.2, 1.25)
        C = (2.2, 0)
        D = (5.1, 0)
        E = (5.1, 4)
        F = (5.8, 4)
        G = (5.8, 1.4)
        H = (8.8, 1.4)
        I = (8.8, 4)
        J = (15.75, 4)
        K = (15.75, 0)
        L = (23.65, 0)
        M = (23.65, 8.25)
        N = (19.15, 8.25)
        O = (19.15, 9.05)
        T = (2.07, 9.05)
        U = (2.07, 6.9)
        V = (0.0, 6.9)

        # Toilet
        P = (11.5, 9.05)
        Q = (11.5, 12.05)
        R = (7.3, 12.05)
        S = (7.3, 9.05)

        # Pillars in toilet
        # Pillars as holes
        t_pillar1 = [(7.3, 10.2), (8.4, 10.2), (8.4, 12.0), (7.3, 12.0)]
        t_pillar2 = [(9.1, 10.2), (9.2, 10.2), (9.2, 12.0), (9.1, 12.0)]
        t_pillar3 = [(9.9, 10.2), (10.0, 10.2), (10.0, 12.0), (9.9, 12.0)]
        t_pillar4 = [(10.7, 10.2), (10.8, 10.2), (10.8, 12.0), (10.7, 12.0)]

        t_pillars = [t_pillar1, t_pillar2, t_pillar3, t_pillar4]

        t_holes = [shift_xy(p, translation_vector) for p in t_pillars]

        # Staff Room

        a = (8.8, 0.0)
        b = (8.8, 4.0)
        c = (11.8, 4.0)
        d = (11.8, 0.0)

        # Pillars in toilet
        # Pillars as holes
        s_pillar1 = [(8.8, 1.4), (9.35, 1.4), (9.35, 3.4), (8.8, 3.4)]
        s_pillar2 = [(11.25, 0.0), (11.8, 0.0), (11.8, 2.6), (11.25, 2.6)]

        s_pillars = [s_pillar1, s_pillar2]

        s_holes = [shift_xy(p, translation_vector) for p in s_pillars]

        # Principal room
        e = (11.9, 0.0)
        f = (11.9, 4.0)
        g = (14.95, 4.0)
        h = (14.95, 0.0)

        # pillars
        # dont think there is any pillars

        # Kitchen

        i = (19.15, 8.25)
        j = (19.15, 9.85)
        k = (20.75, 9.85)
        o = (20.75, 8.25)

        p = (20.75, 8.25)
        q = (20.75, 10.6)
        l = (23.65, 10.6)
        m = (23.65, 8.25)

        # pillars

        k_pillar1 = [(19.15, 9.05), (19.95, 9.05), (19.95, 9.85), (19.15, 9.85)]
        k_pillars = [k_pillar1]
        k_holes = [shift_xy(p, translation_vector) for p in k_pillars]

        exterior = [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, T, U, V, A]
        exterior_shifted = shift_xy(exterior, translation_vector)

        polygon_big_room = Polygon(exterior_shifted, holes)

        # Toilet polygon (closed)
        toilet_points = [P, Q, R, S]
        toilet_shifted = shift_xy(toilet_points, translation_vector)
        toilet_polygon = Polygon(toilet_shifted, t_holes)

        # Staff room
        staff_points = [a, b, c, d]
        staff_shifted = shift_xy(staff_points, translation_vector)
        staff_polygon = Polygon(staff_shifted, s_holes)

        # principal room
        principal_points = [e, f, g, h]
        principal_shifted = shift_xy(principal_points, translation_vector)
        principal_polygon = Polygon(principal_shifted)

        # kitchen
        kitchen_points = [i, j, k, o, p, q, l, m]
        kitchen_shifted = shift_xy(kitchen_points, translation_vector)
        kitchen_polygon = Polygon(kitchen_shifted, k_holes)

        # --- Rasterization setup ---

        def rasterize_polygon(polygon, resolution=0.01):
            minx, miny, maxx, maxy = polygon.bounds
            width = int((maxx - minx) / resolution) + 1
            height = int((maxy - miny) / resolution) + 1

            x_coords = np.linspace(minx, maxx, width)
            y_coords = np.linspace(miny, maxy, height)

            xx, yy = np.meshgrid(x_coords, y_coords)
            points = np.vstack((xx.ravel(), yy.ravel())).T

            mask_flat = vectorized.contains(polygon, points[:, 0], points[:, 1])
            mask = mask_flat.reshape((height, width))

            return mask, (minx, miny, maxx, maxy), resolution

        mask_big_room = rasterize_polygon(polygon_big_room)
        mask_toilet = rasterize_polygon(toilet_polygon)
        mask_kitchen = rasterize_polygon(kitchen_polygon)
        mask_staff = rasterize_polygon(staff_polygon)
        mask_principal = rasterize_polygon(principal_polygon)

        self.valid_meshes = [mask_big_room, mask_staff, mask_principal, mask_kitchen, mask_toilet]

    @staticmethod
    def get_valid_mesh(pos, mesh, translation_vector=None):
        x_t, y_t = pos
        mask, bounds, resolution = mesh
        # Apply translation
        if translation_vector is not None:
            x_t, y_t = x_t + translation_vector[0], y_t + translation_vector[1]
        minx, miny, maxx, maxy = bounds
        ix = int((x_t - minx) / resolution)
        iy = int((y_t - miny) / resolution)

        # Default result
        result = False

        if 0 <= ix < mask.shape[1] and 0 <= iy < mask.shape[0]:
            result = bool(mask[iy, ix])
        return result


def test_polygon_walkable_mask(self):
    # --- Your polygon setup ---

    shift_x = -11.65
    shift_y = -4.5
    translation_vector = (shift_x, shift_y)

    def shift_xy(boundary_points, shift_vector):
        return [(x + shift_vector[0], y + shift_vector[1]) for x, y in boundary_points]

    # Pillars as holes
    pillar1 = [(2.69, 5.25), (3.3, 5.25), (3.3, 6.15), (2.69, 6.15)]
    pillar2 = [(5.69, 5.25), (6.3, 5.25), (6.3, 6.15), (5.69, 6.15)]
    pillar3 = [(8.69, 5.25), (8.92, 5.25), (8.92, 6.15), (8.69, 6.15)]
    pillar4 = [(11.31, 5.25), (11.92, 5.25), (11.92, 6.15), (11.31, 6.15)]
    pillar5 = [(14.69, 5.25), (14.92, 5.25), (14.92, 6.15), (14.69, 6.15)]
    pillar6 = [(17.69, 5.25), (18.3, 5.25), (18.3, 6.15), (17.69, 6.15)]
    pillar7 = [(20.69, 5.25), (21.3, 5.25), (21.3, 6.15), (20.69, 6.15)]
    pillar8 = [(17.685, 0), (17.915, 1.05), (17.915, 1.05), (17.685, 0)]
    pillar9 = [(16.74, 0.0), (16.97, 0.0), (16.97, 0.9), (16.74, 0.9)]
    pillars = [pillar1, pillar2, pillar3, pillar4, pillar5, pillar6, pillar7, pillar8, pillar9]

    holes = [shift_xy(p, translation_vector) for p in pillars]

    # Main Room
    A = (0, 1.25)
    B = (2.2, 1.25)
    C = (2.2, 0)
    D = (5.1, 0)
    E = (5.1, 4)
    F = (5.8, 4)
    G = (5.8, 1.4)
    H = (8.8, 1.4)
    I = (8.8, 4)
    J = (15.75, 4)
    K = (15.75, 0)
    L = (23.65, 0)
    M = (23.65, 8.25)
    N = (19.15, 8.25)
    O = (19.15, 9.05)
    T = (2.07, 9.05)
    U = (2.07, 6.9)
    V = (0.0, 6.9)

    # Toilet
    P = (11.5, 9.05)
    Q = (11.5, 12.05)
    R = (7.3, 12.05)
    S = (7.3, 9.05)

    # Pillars in toilet
    # Pillars as holes
    t_pillar1 = [(7.3, 10.2), (8.4, 10.2), (8.4, 12.0), (7.3, 12.0)]
    t_pillar2 = [(9.1, 10.2), (9.2, 10.2), (9.2, 12.0), (9.1, 12.0)]
    t_pillar3 = [(9.9, 10.2), (10.0, 10.2), (10.0, 12.0), (9.9, 12.0)]
    t_pillar4 = [(10.7, 10.2), (10.8, 10.2), (10.8, 12.0), (10.7, 12.0)]

    t_pillars = [t_pillar1, t_pillar2, t_pillar3, t_pillar4]

    t_holes = [shift_xy(p, translation_vector) for p in t_pillars]

    # Staff Room

    a = (8.8, 0.0)
    b = (8.8, 4.0)
    c = (11.8, 4.0)
    d = (11.8, 0.0)

    # Pillars in toilet
    # Pillars as holes
    s_pillar1 = [(8.8, 1.4), (9.35, 1.4), (9.35, 3.4), (8.8, 3.4)]
    s_pillar2 = [(11.25, 0.0), (11.8, 0.0), (11.8, 2.6), (11.25, 2.6)]

    s_pillars = [s_pillar1, s_pillar2]

    s_holes = [shift_xy(p, translation_vector) for p in s_pillars]

    # Principal room
    e = (11.9, 0.0)
    f = (11.9, 4.0)
    g = (14.95, 4.0)
    h = (14.95, 0.0)

    # pillars
    # dont think there is any pillars

    # Kitchen

    i = (19.15, 8.25)
    j = (19.15, 9.85)
    k = (20.75, 9.85)
    o = (20.75, 8.25)

    p = (20.75, 8.25)
    q = (20.75, 10.6)
    l = (23.65, 10.6)
    m = (23.65, 8.25)

    # pillars

    k_pillar1 = [(19.15, 9.05), (19.95, 9.05), (19.95, 9.85), (19.15, 9.85)]
    k_pillars = [k_pillar1]
    k_holes = [shift_xy(p, translation_vector) for p in k_pillars]

    exterior = [A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, T, U, V, A]
    exterior_shifted = shift_xy(exterior, translation_vector)

    polygon_big_room = Polygon(exterior_shifted, holes)

    # Toilet polygon (closed)
    toilet_points = [P, Q, R, S]
    toilet_shifted = shift_xy(toilet_points, translation_vector)
    toilet_polygon = Polygon(toilet_shifted, t_holes)

    # Staff room
    staff_points = [a, b, c, d]
    staff_shifted = shift_xy(staff_points, translation_vector)
    staff_polygon = Polygon(staff_shifted, s_holes)

    # principal room
    principal_points = [e, f, g, h]
    principal_shifted = shift_xy(principal_points, translation_vector)
    principal_polygon = Polygon(principal_shifted)

    # kitchen
    kitchen_points = [i, j, k, o, p, q, l, m]
    kitchen_shifted = shift_xy(kitchen_points, translation_vector)
    kitchen_polygon = Polygon(kitchen_shifted, k_holes)

    # --- Rasterization setup ---

    def rasterize_polygon(polygon, resolution=0.01):
        minx, miny, maxx, maxy = polygon.bounds
        width = int((maxx - minx) / resolution) + 1
        height = int((maxy - miny) / resolution) + 1

        x_coords = np.linspace(minx, maxx, width)
        y_coords = np.linspace(miny, maxy, height)

        xx, yy = np.meshgrid(x_coords, y_coords)
        points = np.vstack((xx.ravel(), yy.ravel())).T

        mask_flat = vectorized.contains(polygon, points[:, 0], points[:, 1])
        mask = mask_flat.reshape((height, width))

        return mask, (minx, miny, maxx, maxy), resolution

    mask_big_room, bounds, res = rasterize_polygon(polygon_big_room)
    mask_toilet, bounds_toilet, res_toilet = rasterize_polygon(toilet_polygon)
    mask_kitchen, bounds_kitchen, res_kitchen = rasterize_polygon(kitchen_polygon)
    mask_staff, bounds_staff, res_staff = rasterize_polygon(staff_polygon)
    mask_principal, bounds_principal, res_principal = rasterize_polygon(principal_polygon)

    # --- Walkability check function ---

    # --- Testing example output ---
    test_points_big_room = [(11.2, 8.2), (7.6, 3.2), (3.7, 0.3), (10.1, 9.8)]
    test_points_toilet = [(8.0, 10.9), (8.8, 10.7), (10.9, 11.7), (11.4, 11.90)]
    test_points_kitchen = [(19.70, 8.60), (19.80, 7.90), (19.60, 9.40), (22.70, 9.50)]
    test_points_staff = [(9.10, 2.30), (9.90, 0.30), (11.30, 1.10), (11.10, 3.80)]
    test_points_principal = [(11.30, 1.10), (14.50, 0.80)]

    def check_valid(x, y, mask, bounds, resolution, plot_ax=None):
        # Apply translation
        x_t, y_t = x + translation_vector[0], y + translation_vector[1]
        minx, miny, maxx, maxy = bounds
        ix = int((x_t - minx) / resolution)
        iy = int((y_t - miny) / resolution)

        # Default result
        result = False

        if 0 <= ix < mask.shape[1] and 0 <= iy < mask.shape[0]:
            result = bool(mask[iy, ix])

        # If plotting, mark the point
        if plot_ax is not None:
            color = "lime" if result else "red"  # green if walkable, red if blocked
            plot_ax.scatter(ix, iy, color=color, s=30, edgecolor="black")
            plot_ax.text(ix + 1, iy + 1, f"{x:.2f},{y:.2f}",
                         color=color, fontsize=8)

        return result

    fig, axs = plt.subplots(3, 2, figsize=(18, 7))
    axs = axs.flatten()

    # Big Room
    axs[0].imshow(mask_big_room, origin='lower', cmap='Greys')
    axs[0].set_title("Valid Area Mask (Big Room)")
    for pt in test_points_big_room:
        print(f"Point {pt} ->", check_valid(pt[0], pt[1], mask_big_room, bounds, res, axs[0]))

    # Toilet
    axs[1].imshow(mask_toilet, origin='lower', cmap='Greys')
    axs[1].set_title("Valid Area Mask (Toilet)")
    for pt in test_points_toilet:
        print(f"Point {pt} ->", check_valid(pt[0], pt[1], mask_toilet, bounds_toilet, res_toilet, axs[1]))

    # Staff Room
    axs[2].imshow(mask_staff, origin='lower', cmap='Greys')
    axs[2].set_title("Valid Area Mask (Staff)")
    for pt in test_points_staff:
        print(f"Point {pt} ->", check_valid(pt[0], pt[1], mask_staff, bounds_staff, res_staff, axs[2]))

    # Principal Room
    axs[3].imshow(mask_principal, origin='lower', cmap='Greys')
    axs[3].set_title("Valid Area Mask (Principal)")
    for pt in test_points_principal:
        print(f"Point {pt} ->", check_valid(pt[0], pt[1], mask_principal, bounds_principal, res_principal, axs[3]))

    # Kitchen
    axs[4].imshow(mask_kitchen, origin='lower', cmap='Greys')
    axs[4].set_title("Valid Area Mask (Kitchen)")
    for pt in test_points_kitchen:
        print(f"Point {pt} ->", check_valid(pt[0], pt[1], mask_kitchen, bounds_kitchen, res_kitchen, axs[4]))

    if len(axs) > 5:
        axs[5].axis('off')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    pass
