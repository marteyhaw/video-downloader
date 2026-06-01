import { type ButtonHTMLAttributes, type ReactNode } from "react";
import { btnIconDangerClass, btnIconPrimaryClass, btnIconSecondaryClass } from "./ui";

type IconButtonVariant = "secondary" | "primary" | "danger";

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "children"> {
  label: string;
  variant?: IconButtonVariant;
  children: ReactNode;
}

const variantClass: Record<IconButtonVariant, string> = {
  secondary: btnIconSecondaryClass,
  primary: btnIconPrimaryClass,
  danger: btnIconDangerClass,
};

export function IconButton({
  label,
  variant = "secondary",
  className = "",
  type = "button",
  ...props
}: Props) {
  return (
    <button
      type={type}
      aria-label={label}
      className={`${variantClass[variant]} ${className}`.trim()}
      {...props}
    />
  );
}
