import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/authStore";
import { Navigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { Building, Loader2, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import i18n from "@/lib/i18n";

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const toggleLanguage = () => {
    const next = i18n.language === "en" ? "ar" : "en";
    i18n.changeLanguage(next);
  };

  const onSubmit = async (data: LoginFormValues) => {
    try {
      await login(data);
    } catch {
      toast.error(t("auth.loginFailed"));
    }
  };

  return (
    <div className="relative flex min-h-screen">
      {/* Language toggle */}
      <Button
        variant="ghost"
        size="sm"
        onClick={toggleLanguage}
        className="absolute top-4 end-4 z-10 gap-1.5 text-xs font-semibold"
      >
        <Globe className="h-4 w-4" />
        {i18n.language === "en" ? "عربي" : "EN"}
      </Button>

      {/* Left – Login form */}
      <div className="flex flex-1 items-center justify-center p-6 sm:p-12">
        <Card className="w-full max-w-md border-none shadow-none sm:border sm:shadow-sm">
          <CardHeader className="space-y-1 text-center">
            <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <Building className="h-6 w-6" />
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight">
              {t("auth.signIn")}
            </CardTitle>
            <CardDescription>{t("auth.signInDescription")}</CardDescription>
          </CardHeader>

          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">{t("auth.email")}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder={t("auth.emailPlaceholder")}
                  autoComplete="email"
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-xs text-destructive">
                    {t("validation.invalidEmail")}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.password")}</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  {...register("password")}
                />
                {errors.password && (
                  <p className="text-xs text-destructive">
                    {t("validation.passwordMin")}
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isSubmitting}
              >
                {isSubmitting && (
                  <Loader2 className="me-2 h-4 w-4 animate-spin" />
                )}
                {t("auth.signInButton")}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>

      {/* Right – Decorative panel */}
      <div className="hidden flex-1 items-center justify-center bg-gradient-to-br from-primary via-primary/80 to-primary/60 lg:flex">
        <div className="max-w-sm space-y-4 text-center text-primary-foreground">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-white/15 backdrop-blur-sm">
            <Building className="h-9 w-9" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight">Dimora</h1>
          <p className="text-lg text-primary-foreground/80">
            {t("auth.tagline")}
          </p>
        </div>
      </div>
    </div>
  );
}
