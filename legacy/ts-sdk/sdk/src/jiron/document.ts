import pug from 'pug';
import type { JironDocument, JironLink, JironForm, JironField } from './types.js';
import type { SkillDefinition, AgentConfig } from '../types.js';

export function buildRootDocument(config: AgentConfig, skills: SkillDefinition[]): JironDocument {
  return {
    title: `${config.name} — Skill Catalog`,
    links: skills.map(s => ({
      rel: 'skill',
      href: `/skills/${s.name}`,
      title: s.title,
      description: s.description,
    })),
    forms: [],
  };
}

export function buildSkillDocument(skill: SkillDefinition): JironDocument {
  return {
    title: skill.title,
    links: [{ rel: 'catalog', href: '/', title: 'Back to catalog' }],
    forms: [{
      action: `/skills/${skill.name}`,
      method: 'POST',
      title: skill.title,
      fields: skill.fields.map(f => ({
        name: f.name,
        type: f.type,
        label: f.label,
        required: f.required,
        options: f.options,
      })),
    }],
    content: skill.description,
  };
}

export function buildResultDocument(title: string, data: Record<string, unknown>): JironDocument {
  return {
    title,
    links: [{ rel: 'catalog', href: '/', title: 'Back to catalog' }],
    forms: [],
    data,
  };
}

const PUG_TEMPLATE = `
doctype html
html
  head
    title= doc.title
    style.
      body { font-family: system-ui, sans-serif; max-width: 640px; margin: 2rem auto; padding: 0 1rem; }
      a { color: #2563eb; }
      form { margin: 1rem 0; padding: 1rem; border: 1px solid #e5e7eb; border-radius: 8px; }
      label { display: block; margin: 0.5rem 0 0.25rem; font-weight: 600; }
      input, textarea, select { width: 100%; padding: 0.5rem; border: 1px solid #d1d5db; border-radius: 4px; box-sizing: border-box; }
      textarea { min-height: 80px; }
      button { margin-top: 1rem; padding: 0.5rem 1.5rem; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; }
      .data { background: #f9fafb; padding: 1rem; border-radius: 8px; white-space: pre-wrap; font-family: monospace; }
  body
    h1= doc.title
    if doc.content
      p= doc.content
    each link in doc.links
      p
        a(href=link.href)= link.title
        if link.description
          |  — #{link.description}
    each form in doc.forms
      form(action=form.action method=form.method)
        h2= form.title
        each field in form.fields
          label(for=field.name)
            = field.label
            if field.required
              |  *
          if field.type === 'textarea'
            textarea(name=field.name id=field.name required=field.required)
          else if field.type === 'select'
            select(name=field.name id=field.name required=field.required)
              each opt in (field.options || [])
                option(value=opt)= opt
          else
            input(type='text' name=field.name id=field.name required=field.required)
        button(type='submit') Submit
    if doc.data
      h2 Result
      .data= JSON.stringify(doc.data, null, 2)
`;

const renderPug = pug.compile(PUG_TEMPLATE);

export function renderDocument(doc: JironDocument, accept?: string): { body: string; contentType: string } {
  if (accept?.includes('text/html') || accept?.includes('application/vnd.jiron+pug')) {
    return {
      body: renderPug({ doc }),
      contentType: 'text/html; charset=utf-8',
    };
  }
  return {
    body: JSON.stringify(doc, null, 2),
    contentType: 'application/json',
  };
}
