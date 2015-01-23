# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright (C) 2013-2014: SCS Software

# #####  NOTE: Based on SCS Game engine code #####

from mathutils import Vector


def set_direction(forward):
    """Compute the (yaw, pitch, roll) from forward pointing vector.
    Note that the resulting roll is always zero as it cannot be encoded in a 3D vector without additional info.

    :param forward: forward vector
    :type forward: tuple
    :return:
    :rtype:
    """
    import math

    # The "epsilon" was chosen quite randomly.
    # Ought be quite safe - just a safety net against degenerate forward vectors.
    epsilon = 0.0001

    def length(vec):
        return math.sqrt(vec[0] * vec[0] + vec[1] * vec[1] + vec[2] * vec[2])

    def v_clamp(num, minimum, maximum):
        if num < minimum:
            return minimum
        if num > maximum:
            return maximum
        return num

    # Is the forward vector degenerate? Produce "no-rotation" result.
    length = length(forward)
    if length < epsilon:
        pitch = 0.0
        roll = 0.0
        yaw = 0.0
        return pitch, roll, yaw

    # We do not produce any roll, as documented.
    roll = 0.0

    # Compute the pitch directly - arcsin(Y), taking Y component of normalized forward vector.
    pitch = math.degrees(math.asin(v_clamp(forward[1] / length, -1.0, 1.0)))

    # Is the @a forward vector (almost) in the XY plane?
    # Compute the yaw angle directly.
    if math.fabs(forward[2]) < epsilon:
        if forward[0] < 0.0:
            yaw = 90.0
            return pitch, roll, yaw
        if forward[0] > 0.0:
            yaw = 270.0
            return pitch, roll, yaw
        yaw = 0.0
        return pitch, roll, yaw

    # Compute the azimuthal angle.
    # We "realing" the coordinate space -
    # the forward direction will be treated like a virtual "X" axis,
    # the west pointing direction like a virtual "Y" axis.
    # Simple arctan of "X"/"Y" will produce correct azimuthal angle for vectors in positive "X" halfspace.
    # Because we already covered the XY plane above,
    # we know that the "Y" component is never zero (or close to zero).
    # The negative "X" halfspace angles computed by using the arctan function are by 180 degrees off,
    # so we have to adjust for that.
    # After all that, we positive "X" halfspace angles are in the (-90,90) range,
    # and the negative "X" halfpsace angles are in the (90,270) range.
    # Apparently, we must normalize the range (-90,0) to (270,360).
    #
    # The code is quite complex, unfortunately.

    angle = math.degrees(math.atan(forward[0] / forward[2]))
    if forward[2] < 0.0:
        if angle < 0.0:
            angle_bound = 360.0
        else:
            angle_bound = 0.0
        yaw = angle + angle_bound
    else:
        yaw = angle + 180.0

    return pitch, roll, yaw


def compute_bernstein(float_t):
    """Evaluate the cubic Bernstein polynomials at given parameter
    and return the bernstein polynomial coefficients..

    :param float_t:
    :type float_t: float
    """
    q = 1.0 - float_t
    f1 = q * q * q
    f2 = 3.0 * float_t * q * q
    f3 = 3.0 * float_t * float_t * q
    f4 = float_t * float_t * float_t
    return f1, f2, f3, f4


def evaluate_bezier_curve(vec1, vec2, vec3, vec4, float_t):
    """Evaluate the cubic Bezier curve at given parameter point
    and return the point generated by given bezier curve and parameter point "float_t".
    Standard Bezier curve is a linear combination of control points (vec1, vec2, vec3, vec4),
    weighted by factors obtained from cubic Bernstein polynomials evaluated at point (float_t).

    :param vec1:
    :type vec1: tuple
    :param vec2:
    :type vec2: tuple
    :param vec3:
    :type vec3: tuple
    :param vec4:
    :type vec4: tuple
    :param float_t:
    :type float_t: float
    :return:
    :rtype: mathutils.Vector
    """
    from mathutils import Vector

    c = compute_bernstein(float_t)
    f1 = c[0] * vec1[0] + c[1] * vec2[0] + c[2] * vec3[0] + c[3] * vec4[0]
    f2 = c[0] * vec1[1] + c[1] * vec2[1] + c[2] * vec3[1] + c[3] * vec4[1]
    f3 = c[0] * vec1[2] + c[1] * vec2[2] + c[2] * vec3[2] + c[3] * vec4[2]
    return Vector((f1, f2, f3))


def smooth_curve(point1, tang1, point2, tang2, coef):
    """Smooth continuous curve helper based on piecewise cubic bezier curves
    designed for waypoint navigation.

    Feed the function with two waypoint positions (point1 and point2), and the tangential vectors
    in those positions (tang1 and tang2). The coef parameter can range from 0.0 to 1.0. As
    the coef grows (with time in the system), the function generates appropriate positions and
    tangentials along a bezier curve passing through those two waypoints.

    Once coef is getting past 1.0, it is time for you to generate a new waypoint and direction,
    and once "decrement coef by 1.0" when adding a new curve segment, copy the values from
    <point2, tang2> into <point1, tang1>. This way you will insure the next curve segment will not
    only be continuous, but also that the transition will be smooth.

    Note that the length of the tangential vectors affects the curvature of the segments!
    Usually, you will want the length of the tangential vectors to be in 10's of percentage
    points of the length of the <point2-point1> vector.

    :param point1: position of the starting waypoint
    :type point1: mathutils.Vector
    :param tang1: tangential vector (direction vector) at the starting waypoint
    :type tang1: mathutils.Quaternion
    :param point2: position of the ending waypoint
    :type point2: mathutils.Vector
    :param tang2: tangential vector (direction vector) at the ending waypoint
    :type tang2: mathutils.Quaternion
    :param coef: coefficient ranging from 0.0 to 1.0 suggesting how far from start to end to generate a point
    :type coef: float
    :return:
    :rtype: mathutils.Vector
    """
    pp1 = point1
    pp2 = point1 + tang1
    pp3 = point2 - tang2
    pp4 = point2

    # Compute position along the Bezier curve.
    pos = evaluate_bezier_curve(pp1, pp2, pp3, pp4, coef)

    # Compute appropriate tangential vector along the curve.
    return pos


def compute_smooth_curve_length(point1, tang1, point2, tang2, measure_steps):
    """Takes two points in space and their tangents and returns length of the curve as a float.
    The accuracy of measuring can be controlled by "measure_steps" parameter.

    :param point1: position of the starting waypoint
    :type point1: mathutils.Vector
    :param tang1: tangential vector (direction vector) at the starting waypoint
    :type tang1: mathutils.Quaternion
    :param point2: position of the ending waypoint
    :type point2: mathutils.Vector
    :param tang2: tangential vector (direction vector) at the ending waypoint
    :type tang2: mathutils.Quaternion
    :param measure_steps:
    :type measure_steps: int
    :return:
    :rtype: float
    """
    step_size = 1.0 / float(measure_steps)
    coef = step_size
    lenth = 0.0
    start_pos = point1
    for ii in range(measure_steps):
        cpos = smooth_curve(point1, tang1, point2, tang2, coef)
        le = start_pos - cpos
        lenth += le.length
        start_pos = cpos
        coef += step_size
    return lenth


def compute_curve(obj_0, point1, obj_1, point2, curve_steps):
    from mathutils import Vector

    tang1 = obj_0.matrix_world.to_quaternion() * Vector((0, 1, 0))
    tang2 = obj_1.matrix_world.to_quaternion() * Vector((0, 1, 0))
    le = compute_smooth_curve_length(point1, tang1, point2, tang2, 300)
    curve_data = {'curve_points': []}
    # if obj_0.scs_props.locator_prefab_np_crossroad:
    # curve_data['curve_color0'] = (0, 0, 1)
    # elif obj_0.scs_props.locator_prefab_np_low_prior:
    # curve_data['curve_color0'] = (0.5, 0.5, 1)
    # elif obj_0.scs_props.locator_prefab_np_allowed_veh == 'to':
    # curve_data['curve_color0'] = (0, 1, 0)
    # elif obj_0.scs_props.locator_prefab_np_allowed_veh == 'nt':
    # curve_data['curve_color0'] = (1, 0, 0)
    # else:
    # curve_data['curve_color0'] = (bpy.context.scene.scs_props.curve_base_color.r, bpy.context.scene.scs_props.curve_base_color.g,
    # bpy.context.scene.scs_props.curve_base_color.b)
    # if obj_0.scs_props.locator_prefab_np_blinker == 'rb':
    # curve_data['curve_color1'] = (0.2, 0.7, 1)
    # elif obj_0.scs_props.locator_prefab_np_blinker == 'lb':
    # curve_data['curve_color1'] = (1, 0.2, 0.7)
    # else:
    # curve_data['curve_color1'] = (bpy.context.scene.scs_props.curve_base_color.r, bpy.context.scene.scs_props.curve_base_color.g,
    # bpy.context.scene.scs_props.curve_base_color.b)
    # curve_steps = 16
    # curve_steps = bpy.context.scene.scs_props.curve_segments
    # curve_data['curve_steps'] = curve_steps
    for segment in range(curve_steps):
        coef = float(segment / curve_steps)
        # print('coef: %s' % coef)
        pos = smooth_curve(point1, tang1 * (le / 3), point2, tang2 * (le / 3), coef)
        # print('pos: %s' % str(pos))
        curve_data['curve_points'].append(pos)
        # points['point ' + str(coef)] = Vector(pos)
    curve_data['curve_points'].append(point2)  # last point
    return curve_data


def curves_intersect(curve1, curve2, part_count=10):
    """
    :param curve1:
    :type curve1: io_scs_tools.internals.structure.SectionData
    :param curve2:
    :type curve2: io_scs_tools.internals.structure.SectionData
    :param part_count:
    :return:
    """
    length1 = curve1.get_prop_value("Length")[1][0]
    length2 = curve2.get_prop_value("Length")[1][0]
    step1 = length1 / part_count
    step2 = length2 / part_count
    pos1 = 0
    epsilon = 0.01

    for i in range(part_count):
        # curve1_point1 = get_prop(get_section(get_section(curve1, "Bezier"), "Start").props, "Position")[1]
        curve1_point1 = curve1.get_section("Bezier").get_section("Start").get_prop_value("Position")[1]
        # curve1_tang1 = Vector(get_prop(get_section(get_section(curve1, "Bezier"), "Start").props, "Direction")[1])
        curve1_tang1 = Vector(curve1.get_section("Bezier").get_section("Start").get_prop_value("Direction")[1])
        # curve1_point2 = get_prop(get_section(get_section(curve1, "Bezier"), "End").props, "Position")[1]
        curve1_point2 = curve1.get_section("Bezier").get_section("End").get_prop_value("Position")[1]
        # curve1_tang2 = Vector(get_prop(get_section(get_section(curve1, "Bezier"), "End").props, "Direction")[1])
        curve1_tang2 = Vector(curve1.get_section("Bezier").get_section("End").get_prop_value("Direction")[1])
        start1 = smooth_curve(curve1_point1, curve1_tang1, curve1_point2, curve1_tang2, pos1 / length1)
        end1 = smooth_curve(curve1_point1, curve1_tang1, curve1_point2, curve1_tang2, (pos1 + step1) / length1)

        pos2 = 0
        for j in range(part_count):
            # curve2_point1 = get_prop(get_section(get_section(curve2, "Bezier"), "Start").props, "Position")[1]
            curve2_point1 = curve2.get_section("Bezier").get_section("Start").get_prop_value("Position")[1]
            # curve2_tang1 = Vector(get_prop(get_section(get_section(curve2, "Bezier"), "Start").props, "Direction")[1])
            curve2_tang1 = Vector(curve2.get_section("Bezier").get_section("Start").get_prop_value("Direction")[1])
            # curve2_point2 = get_prop(get_section(get_section(curve2, "Bezier"), "End").props, "Position")[1]
            curve2_point2 = curve2.get_section("Bezier").get_section("End").get_prop_value("Position")[1]
            # curve2_tang2 = Vector(get_prop(get_section(get_section(curve2, "Bezier"), "End").props, "Direction")[1])
            curve2_tang2 = Vector(curve2.get_section("Bezier").get_section("End").get_prop_value("Direction")[1])
            start2 = smooth_curve(curve2_point1, curve2_tang1, curve2_point2, curve2_tang2, pos2 / length2)
            end2 = smooth_curve(curve2_point1, curve2_tang1, curve2_point2, curve2_tang2, (pos2 + step2) / length2)
            pos2 += step2

            # if not 'moc vysoko':
            denom = ((end2[2] - start2[2]) * (end1[0] - start1[0])) - ((end2[0] - start2[0]) * (end1[2] - start1[2]))
            nume_a = ((end2[0] - start2[0]) * (start1[2] - start2[2])) - ((end2[2] - start2[2]) * (start1[0] - start2[0]))
            nume_b = ((end1[0] - start1[0]) * (start1[2] - start2[2])) - ((end1[2] - start1[2]) * (start1[0] - start2[0]))

            if abs(denom) < epsilon:
                continue

            mu_a = nume_a / denom
            mu_b = nume_b / denom
            if mu_a < 0 or mu_a > 1 or mu_b < 0 or mu_b > 1:
                continue

            if (mu_a < epsilon and i == 0) or (mu_b < epsilon and j == 0):
                return None
            if (mu_a > 1 - epsilon and i == part_count - 1) or (mu_b > 1 - epsilon and j == part_count - 1):
                return None

            curve_intersect = Vector((0, 0, 0))
            curve_intersect.x = start1[0] + mu_a * (end1[0] - start1[0])
            curve_intersect.y = (start1[1] + end1[1] + start2[1] + end2[1]) / 4.0
            curve_intersect.z = start1[2] + mu_a * (end1[2] - start1[2])

            return curve_intersect

        pos1 += step1

    return None


def compute_curve_intersections(nav_curve_sections):
    """
    :param nav_curve_sections: Navigation Curves' data section
    :type nav_curve_sections: list[io_scs_tools.internals.structure.SectionData]
    :return: ...?
    :rtype: dict
    """
    curve_dict = {'START': [], 'END': [], 'CROSS': []}

    for nav_curve_section_i, nav_curve_section in enumerate(nav_curve_sections):
        if nav_curve_section.get_prop_value("NextCurves")[1] != -1:
            curve_dict['START'].append((nav_curve_section, None, 0))
        if nav_curve_section.get_prop_value("PrevCurves")[1] != -1:
            curve_dict['END'].append((nav_curve_section, None, 0))
        for curve_index in range(nav_curve_section_i + 1, len(nav_curve_sections)):
            curve_to_test = nav_curve_sections[curve_index]
            curve_intersect = curves_intersect(nav_curve_section, curve_to_test)
            print('curve_intersect: %s' % str(curve_intersect))
            if curve_intersect:
                curve_dict['CROSS'].append((nav_curve_section, curve_to_test, curve_intersect))

    return curve_dict


'''
def define_curve(lines, obj_0, obj_1):
    from mathutils import Vector

    point1 = Vector(obj_0.location)
    # tang1 = Vector((-1, 0, 0))
    tang1 = obj_0.matrix_world.to_quaternion() * Vector((0, 1, 0))
    # point2 = Vector((4, -1, 0))
    point2 = Vector(obj_1.location)
    # tang2 = Vector((1, 0, 0))
    tang2 = obj_1.matrix_world.to_quaternion() * Vector((0, 1, 0))
    le = compute_smooth_curve_length(point1, tang1, point2, tang2, 300)
    line = {}
    if obj_0.scs_props.locator_prefab_np_crossroad:
        line['line_color1'] = (0, 0, 1)
    elif obj_0.scs_props.locator_prefab_np_low_prior:
        line['line_color1'] = (0.5, 0.5, 1)
    elif obj_0.scs_props.locator_prefab_np_allowed_veh == 'to':
        line['line_color1'] = (0, 1, 0)
    elif obj_0.scs_props.locator_prefab_np_allowed_veh == 'nt':
        line['line_color1'] = (1, 0, 0)
    else:
        line['line_color1'] = (bpy.context.scene.scs_props.curve_base_color.r, bpy.context.scene.scs_props.curve_base_color.g,
                               bpy.context.scene.scs_props.curve_base_color.b)
    if obj_0.scs_props.locator_prefab_np_blinker == 'rb':
        line['line_color2'] = (0.2, 0.7, 1)
    elif obj_0.scs_props.locator_prefab_np_blinker == 'lb':
        line['line_color2'] = (1, 0.2, 0.7)
    else:
        line['line_color2'] = (bpy.context.scene.scs_props.curve_base_color.r, bpy.context.scene.scs_props.curve_base_color.g,
                               bpy.context.scene.scs_props.curve_base_color.b)
    curve_steps = 15
    line['line_steps'] = curve_steps
    line['line_points'] = []
    for segment in range(curve_steps):
        coef = float(segment / curve_steps)
        # print('coef: %s' % coef)
        pos = utils_curve.smooth_curve(point1, tang1 * (le / 3), point2, tang2 * (le / 3), coef)
        # print('pos: %s' % str(pos))
        # lines[obj_0.name].append(pos)
        line['line_points'].append(pos)
        # points['point ' + str(coef)] = Vector(pos)
    lines[str(obj_0.name + obj_1.name)] = line
    return lines
'''