import json
from odoo import _, http
from odoo.http import request, content_disposition
import base64
import zipfile
import io

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

class OpenController(http.Controller):
    _t = 4
    
    @http.route('/hello', auth='public')
    def hello(self):
        return "Hello World"
    
    @http.route('/hello/<string:name>', auth='public')
    def hello_name(self, name):
        return "Hello %s" % name
    
    @http.route('/test2', auth='public')
    def back_to_web(self):
        return http.redirect_with_hash('/web')
    
    @http.route(['/courses', '/courses/page/<int:page>', '/' ], auth='public', website=True)
    def courses(self, page=0):        
        try:
            search = request.params.get('search')
            if search is not None:
                courses = request.env['open_academy.course'].sudo().search([('title', 'ilike', search)])
            else:
                courses = request.env['open_academy.course'].sudo().search([])
        except Exception as e:
            return "<h1>There is an error in the API</h1> %s" % e
        
        sort_by = request.params.get('sort_by')
        if sort_by is None:
            courses = sorted(courses, key=lambda r: r.title)
        else:
            sort_criteria = sort_by
            reverse = sort_by.startswith('-')
            if reverse is True:
                sort_criteria = sort_by[1:]
                
            if sort_criteria == 'responsible':
                courses = sorted(courses, key=lambda x: x.responsible.name, reverse=reverse)
            else:
                courses = sorted(courses, key=lambda x: getattr(x, sort_criteria), reverse=reverse)
            
        filter_by = request.params.get('filter_by')
        if filter_by is not None:
            if filter_by != 'all':
                courses = [course for course in courses if getattr(course, 'type') == filter_by]
                
        available = request.params.get('available')
        if available is not None:
            if available == 'yes':
                for course in courses:
                    for session in course.sessions:
                        if session.taken_seats != 100:
                            continue
                        else:
                            courses.remove(course)
                            break

        total = len(courses)
        pager = request.website.pager(
            url="/courses",
            total=total ,
            page=page,
            step=self._t,
            url_args={
                'search': search or None, 
                'sort_by': sort_by or None,
                'filter': filter_by or None,
                'available': available or None,
            },
        )
        
        offset = pager ['offset']
        courses = courses [offset: offset + self._t]
 
        return request.render('open_academy_controllers.courses_template', {
            'course': courses,
            'pager': pager,
            'filter_by': filter_by,
            'sort_by': sort_by,
            'available': available,
        })
        
      
    @http.route(['/course/<int:id>', '/course/<int:id>/page/<int:page>'], auth='public', website=True)
    def course(self, id, page=0):
        
        try:
            course = request.env['open_academy.course'].sudo().search([('id', '=', id)]) 
            sessions = request.env['open_academy.session'].sudo().search([('course', '=', id)])
        except Exception as e:
            return "<h1>There is an error in the API</h1> %s" % e
        
        sort_by = request.params.get('sort_by')
        if sort_by is None:
            sessions = sorted(sessions, key=lambda r: r.initial_date)
        else:
            sort_criteria = sort_by
            reverse = sort_by.startswith('-')
            if reverse is True:
                sort_criteria = sort_by[1:]

            if sort_criteria == 'instructor':
                sessions = sorted(sessions, key=lambda x: x.instructor.name, reverse=reverse) 
            else:   
                sessions = sorted(sessions, key=lambda x: getattr(x, sort_criteria), reverse=reverse)      
                
        available = request.params.get('available')
        if available is not None:
            if available == 'yes':
                for session in sessions:
                    if session.taken_seats == 100.0:
                        sessions.remove(session)
                        
                        
        pager = request.website.pager(
            url="/course/%s" % id,
            total=len(sessions),
            page=page,
            step=self._t,
            url_args={
                'sort_by': sort_by or None,
                'available': available or None,
            },
        )
        
        offset = pager ['offset']
        sessions = sessions [offset: offset + self._t]
        
        return request.render('open_academy_controllers.course_id_template', {
            'course': course,
            'sessions': sessions,
            'sort_by': sort_by,
            'pager': pager,
            'available': available,
        })            
        
    @http.route('/courses-json', auth='public')
    def course_json(self):
        try:
            courses = request.env['open_academy.course'].search([])
        except:
            return "<h1>There is an error in the API</h1>"
        
        results = []
        for course in courses:
            results.append({
                'title': course.title,
                'description': course.description,
            })
            
        return request.make_response(json.dumps(results), headers=[('Content-Type', 'application/json')])
        

        
    @http.route(['/my', '/my/home'], auth='public', website=True)
    def my_sessions(self):  
        
        if request.session.uid:      
            try:
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                sessions = request.env['open_academy.session'].search([('attendees', 'in', partner.id)])
            except:
                return "<h1>There is an error in the API</h1>"
        else: 
            return http.redirect_with_hash('/web/login')
        
        return request.render('open_academy_controllers.sessions_menu', {
            'num_sessions': len(sessions),
        })
        

    @http.route('/course/comment/<int:id>', auth='public', website=True, methods=['POST'])
    def comment(self, id):
        if request.session.uid:
            try:
                comment = request.params['comment']
                course = request.env['open_academy.course'].search([('id', '=', id)])
                user = request.env['res.users'].search([('id', '=', request.session.uid)])
                partner = request.env['res.partner'].search([('id', '=', user.partner_id.id)])
                c = request.env['mail.message'].create({
                    'model': 'open_academy.course',
                    'res_id': course.id,
                    'body': comment,
                    'message_type': 'comment',
                    'author_id': partner.id,
                })
                course.comments = [(4, c.id)]
            except:
                return "<h1>There is an error adding the comment</h1>"
            
            return http.redirect_with_hash('/course/' + str(course.id))
            
        else:
            return http.redirect_with_hash('/web/login')
        
    @http.route('/course/comment/delete/<int:id>', auth='public', website=True, methods=['POST'])
    def delete_comment(self, id):        
        if request.session.uid:
            try:
                comment_id = request.params['comment_id']
                course = request.env['open_academy.course'].search([('id', '=', id)])
                c = request.env['mail.message'].search([('id', '=', comment_id)])
                course.comments = [(3, c.id)]
                c.unlink()
            except:
                return "<h1>There is an error deleting the comment</h1>"
            
            return http.redirect_with_hash('/course/' + str(course.id))
            
        else:
            return http.redirect_with_hash('/web/login')
        
    @http.route('/course/<int:id>/documents', auth='public', website=True)
    def documents(self, id):
        try:
            course = request.env['open_academy.course'].sudo().search([('id', '=', id)])
            documents = course.documents
            if not documents:
                return "<h1>No documents found for this course</h1>"
            else:
                zip_filename = course.title + ".zip"
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for document in documents:
                        data = base64.b64decode(document.datas)
                        zip_file.writestr(document.name, data)
                headers = [
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition', content_disposition(zip_filename))
                ]
                return request.make_response(zip_buffer.getvalue(), headers)
        except Exception as e:
            return "<h1>There is an error in the API</h1> " + str(e)
    
                
                