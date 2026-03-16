export interface JironDocument {
  title: string;
  links: JironLink[];
  forms: JironForm[];
  data?: Record<string, unknown>;
  content?: string;
}

export interface JironLink {
  rel: string;
  href: string;
  title: string;
  description?: string;
}

export interface JironForm {
  action: string;
  method: 'GET' | 'POST';
  title: string;
  fields: JironField[];
}

export interface JironField {
  name: string;
  type: 'text' | 'textarea' | 'select';
  label: string;
  required?: boolean;
  options?: string[];
}
