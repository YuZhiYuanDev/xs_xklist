#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取真实测试数据
"""

import json
from course_selector import CourseSelector, ConfigManager

# 加载配置
config_manager = ConfigManager('config.json')
config = config_manager.load()

# 创建选择器
selector = CourseSelector(config.cookies)

# 获取课程列表
print("正在获取课程列表...")
courses = selector.get_course_list()

print(f"\n获取到 {len(courses)} 门课程")
print("\n" + "=" * 80)

# 显示前5门课程的详细信息
for i, course in enumerate(courses[:5], 1):
    print(f"\n课程 {i}:")
    print(f"  ID: {course.id}")
    print(f"  名称: {course.name}")
    print(f"  类别: {course.category}")
    print(f"  教师: {course.teacher}")
    print(f"  学分: {course.credit}")
    print(f"  时间: {course.schedule}")
    print(f"  容量: {course.capacity} | 已选: {course.enrolled} | 剩余: {course.remaining}")
    print(f"  EventTarget: {course.enroll_event_target}")
    print(f"  EventArgument: {course.enroll_event_argument}")

# 保存测试数据
test_data = {
    'courses': [
        {
            'id': c.id,
            'name': c.name,
            'category': c.category,
            'teacher': c.teacher,
            'credit': c.credit,
            'schedule': c.schedule,
            'capacity': c.capacity,
            'enrolled': c.enrolled,
            'remaining': c.remaining,
            'enroll_event_target': c.enroll_event_target,
            'enroll_event_argument': c.enroll_event_argument
        }
        for c in courses[:5]
    ],
    'form_fields': selector.form_fields
}

with open('test_data.json', 'w', encoding='utf-8') as f:
    json.dump(test_data, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 80)
print("测试数据已保存到 test_data.json")
