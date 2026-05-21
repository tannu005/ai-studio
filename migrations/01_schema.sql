-- Create custom types for Role and Status
CREATE TYPE user_role AS ENUM ('admin', 'user');
CREATE TYPE task_status AS ENUM ('pending', 'assigned', 'in_progress', 'submitted', 'accepted', 'revision_requested');

-- 1. Create Users Table
CREATE TABLE public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create Tasks Table
CREATE TABLE public.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'pending',
    product_image_url TEXT NOT NULL,
    assigned_to UUID REFERENCES public.users(id) ON DELETE SET NULL,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL,
    revision_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Create Generated Images Table
CREATE TABLE public.generated_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES public.tasks(id) ON DELETE CASCADE,
    image_type TEXT NOT NULL, -- e.g., 'white_bg', 'theme_luxury_velvet', 'model_front', etc.
    image_url TEXT NOT NULL,
    prompt_used TEXT,
    angle TEXT,               -- 'front', 'side', 'closeup'
    metadata JSONB DEFAULT '{}'::jsonb,
    is_final BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Create Audit Logs Table
CREATE TABLE public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name TEXT NOT NULL,
    action TEXT NOT NULL,     -- 'INSERT', 'UPDATE', 'DELETE'
    row_id TEXT NOT NULL,
    performed_by UUID,        -- User ID who made change
    old_data JSONB,
    new_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Create Policies

-- Users Table Policies
CREATE POLICY "Users can read all profiles" ON public.users
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Users can update their own profile" ON public.users
    FOR UPDATE TO authenticated USING (auth.uid() = id);

CREATE POLICY "Admins have full access on profiles" ON public.users
    FOR ALL TO authenticated USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- Tasks Table Policies
CREATE POLICY "Users can select their assigned tasks" ON public.tasks
    FOR SELECT TO authenticated USING (
        assigned_to = auth.uid() OR 
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Users can update their assigned tasks" ON public.tasks
    FOR UPDATE TO authenticated USING (
        assigned_to = auth.uid() OR 
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "Admins have full access on tasks" ON public.tasks
    FOR ALL TO authenticated USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- Generated Images Table Policies
CREATE POLICY "Users can view images for their assigned tasks" ON public.generated_images
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.tasks 
            WHERE tasks.id = generated_images.task_id AND 
            (tasks.assigned_to = auth.uid() OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'))
        )
    );

CREATE POLICY "Users can insert images for their assigned tasks" ON public.generated_images
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.tasks 
            WHERE tasks.id = generated_images.task_id AND 
            (tasks.assigned_to = auth.uid() OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'))
        )
    );

CREATE POLICY "Users can delete images for their assigned tasks" ON public.generated_images
    FOR DELETE TO authenticated USING (
        EXISTS (
            SELECT 1 FROM public.tasks 
            WHERE tasks.id = generated_images.task_id AND 
            (tasks.assigned_to = auth.uid() OR EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin'))
        )
    );

-- Audit Logs Table Policies
CREATE POLICY "Admins can view all audit logs" ON public.audit_logs
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- Trigger function to log database changes automatically to audit_logs
CREATE OR REPLACE FUNCTION public.process_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO public.audit_logs (table_name, action, row_id, performed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.id::text, auth.uid(), row_to_json(OLD)::jsonb, NULL);
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO public.audit_logs (table_name, action, row_id, performed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id::text, auth.uid(), row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO public.audit_logs (table_name, action, row_id, performed_by, old_data, new_data)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id::text, auth.uid(), NULL, row_to_json(NEW)::jsonb);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add Audit Triggers to tables
CREATE TRIGGER audit_users_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.users
FOR EACH ROW EXECUTE FUNCTION public.process_audit_log();

CREATE TRIGGER audit_tasks_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.tasks
FOR EACH ROW EXECUTE FUNCTION public.process_audit_log();

CREATE TRIGGER audit_generated_images_trigger
AFTER INSERT OR UPDATE OR DELETE ON public.generated_images
FOR EACH ROW EXECUTE FUNCTION public.process_audit_log();
