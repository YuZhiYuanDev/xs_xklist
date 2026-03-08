"""
获取真实HTML响应数据用于测试
"""

import json
from pathlib import Path
from course_selector import CourseSelector, ConfigManager


def fetch_html_responses():
    """获取真实的HTML响应数据"""
    # 加载配置
    config_manager = ConfigManager('config.json')
    config = config_manager.load()
    
    # 创建选择器
    selector = CourseSelector(config.cookies)
    
    # 获取课程列表页面HTML
    print("正在获取课程列表页面...")
    courses = selector.get_course_list()
    
    if not courses:
        print("未获取到课程数据")
        return
    
    # 保存HTML响应数据
    html_data = {
        'course_list_html': selector._last_response_text if hasattr(selector, '_last_response_text') else '',
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
            for c in courses
        ],
        'form_fields': selector._form_fields
    }
    
    # 保存到文件
    output_file = Path('test_html_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(html_data, f, ensure_ascii=False, indent=2)
    
    print(f"HTML数据已保存到 {output_file}")
    print(f"共获取 {len(courses)} 门课程")


if __name__ == '__main__':
    fetch_html_responses()
