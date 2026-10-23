export const CERTIFICATE_TYPES = {
  CRT: {
    title: "Campus Recruitment Training (CRT)",
    description: "for successfully completing the 16-week intensive Campus Recruitment Training covering advanced Data Structures, Algorithms, Aptitude Assessments, and Corporate Communication."
  },
  FDP: {
    title: "Faculty Development Programme (FDP)",
    description: "for successfully completing the Faculty Development Programme on Modern Placement Technologies, Pedagogy, and Industry-Aligned Curriculums."
  },
  WORKSHOP: {
    title: "Technical Workshop Certification",
    description: "for active participation and successful completion of the Hands-on Technical Workshop on Full Stack Engineering and Systems Architecture."
  },
  HACKATHON: {
    title: "Hackathon Achievement Certification",
    description: "for outstanding performance, innovation, and technical execution in the Skill Tank Placement Prep Hackathon."
  },
  INTERNSHIP: {
    title: "Internship Experience Certification",
    description: "for successfully completing the Industry Placement Preparatory Internship and demonstrating proficiency in software development, teamwork, and system deployment."
  },
  PLACEMENT: {
    title: "Placement Excellence Award",
    description: "for demonstrating outstanding technical readiness and securing a placement offer under the CareerOS Partner Placement Intelligence program."
  }
};

export function renderCertificateToCanvas(canvas, data) {
  return new Promise((resolve) => {
    const ctx = canvas.getContext("2d");
    const width = 1200;
    const height = 820;
    
    // Set high-res backing size
    canvas.width = width;
    canvas.height = height;

    // 1. Background (Cream)
    ctx.fillStyle = "#faf6f0";
    ctx.fillRect(0, 0, width, height);

    // 2. Thick Outer Border (Charcoal)
    ctx.lineWidth = 14;
    ctx.strokeStyle = "#111827";
    ctx.strokeRect(15, 15, width - 30, height - 30);

    // 3. Thin Inner Border (Accent Orange)
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#ea580c";
    ctx.strokeRect(28, 28, width - 56, height - 56);

    // 4. Decorative Corner Brackets (Accent Orange)
    ctx.strokeStyle = "#ea580c";
    ctx.lineWidth = 4;
    
    // Top-Left
    ctx.beginPath(); ctx.moveTo(40, 65); ctx.lineTo(40, 40); ctx.lineTo(65, 40); ctx.stroke();
    // Top-Right
    ctx.beginPath(); ctx.moveTo(width - 65, 40); ctx.lineTo(width - 40, 40); ctx.lineTo(width - 40, 65); ctx.stroke();
    // Bottom-Left
    ctx.beginPath(); ctx.moveTo(40, height - 65); ctx.lineTo(40, height - 40); ctx.lineTo(65, height - 40); ctx.stroke();
    // Bottom-Right
    ctx.beginPath(); ctx.moveTo(width - 65, height - 40); ctx.lineTo(width - 40, height - 40); ctx.lineTo(width - 40, height - 65); ctx.stroke();

    // 5. Header Logos & Badges
    ctx.textAlign = "left";
    ctx.fillStyle = "#111827";
    ctx.font = "bold 15px monospace";
    ctx.fillText("§ SKILL TANK PARTNER", 60, 95);

    ctx.textAlign = "right";
    ctx.fillStyle = "#ea580c";
    ctx.font = "bold 15px sans-serif";
    ctx.fillText((data.collegeName || "PARTNER INSTITUTION").toUpperCase(), width - 60, 95);

    // 6. Certificate Title Label
    ctx.textAlign = "center";
    ctx.fillStyle = "#6b7280";
    ctx.font = "bold 13px monospace";
    // Simulated letter spacing
    const certLabel = "C E R T I F I C A T E   O F   C O M P L E T I O N";
    ctx.fillText(certLabel, width / 2, 195);

    // 7. Certificate Program Title
    ctx.fillStyle = "#ea580c";
    ctx.font = "italic bold 34px Georgia, serif";
    ctx.fillText(data.title, width / 2, 250);

    // 8. Presented To
    ctx.fillStyle = "#4b5563";
    ctx.font = "italic 16px Georgia, serif";
    ctx.fillText("This certificate is proudly presented to", width / 2, 310);

    // 9. Recipient Student Name
    ctx.fillStyle = "#111827";
    ctx.font = "bold 38px sans-serif";
    ctx.fillText(data.studentName, width / 2, 370);

    // Underline for name
    ctx.strokeStyle = "#ea580c";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(width / 2 - 200, 385);
    ctx.lineTo(width / 2 + 200, 385);
    ctx.stroke();

    // 10. Roll number and Branch
    ctx.fillStyle = "#374151";
    ctx.font = "bold 13px monospace";
    ctx.fillText(`ROLL NO: ${data.rollNumber || "N/A"}   |   BRANCH: ${(data.branch || "CSE").toUpperCase()}`, width / 2, 420);

    // 11. Description Text wrapping
    ctx.fillStyle = "#4b5563";
    ctx.font = "15px Georgia, serif";
    
    function wrapText(context, text, x, y, maxWidth, lineHeight) {
      const words = text.split(" ");
      let line = "";
      let currentY = y;
      for (let n = 0; n < words.length; n++) {
        let testLine = line + words[n] + " ";
        let metrics = context.measureText(testLine);
        let testWidth = metrics.width;
        if (testWidth > maxWidth && n > 0) {
          context.fillText(line, x, currentY);
          line = words[n] + " ";
          currentY += lineHeight;
        } else {
          line = testLine;
        }
      }
      context.fillText(line, x, currentY);
    }
    wrapText(ctx, data.description, width / 2, 465, 800, 24);

    // 12. Signatures & Metadata Footer
    const footerY = 660;

    // Left Signature: Placement Director (TPO)
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(80, footerY); ctx.lineTo(300, footerY); ctx.stroke();
    
    ctx.fillStyle = "#111827";
    ctx.font = "italic bold 18px Georgia, serif";
    ctx.fillText(data.signatureTpo || "Dr. Neil Gogte", 190, footerY - 15);
    ctx.font = "bold 11px sans-serif";
    ctx.fillText("PLACEMENT DIRECTOR", 190, footerY + 22);
    ctx.font = "9px monospace";
    ctx.fillText("Institution Partner", 190, footerY + 34);

    // Right Signature: Skill Tank Signatory
    ctx.beginPath(); ctx.moveTo(width - 300, footerY); ctx.lineTo(width - 80, footerY); ctx.stroke();
    
    ctx.fillStyle = "#111827";
    ctx.font = "italic bold 18px Georgia, serif";
    ctx.fillText(data.signatureSkillTank || "Skill Tank Director", width - 190, footerY - 15);
    ctx.font = "bold 11px sans-serif";
    ctx.fillText("SKILL TANK LEADER", width - 190, footerY + 22);
    ctx.font = "9px monospace";
    ctx.fillText("Authorized Signatory", width - 190, footerY + 34);

    // 13. Metadata details (Date and ID)
    ctx.fillStyle = "#9ca3af";
    ctx.font = "9px monospace";
    ctx.fillText(`ID: ${data.certId}`, 190, footerY + 65);
    ctx.fillText(`DATE: ${data.date}`, width - 190, footerY + 65);

    // 14. Center QR Code Loading with beautiful local fallback
    const qrImg = new window.Image();
    qrImg.crossOrigin = "anonymous";
    const verifyUrl = `${window.location.origin}/verify/${data.certId}`;
    qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=90x90&data=${encodeURIComponent(verifyUrl)}`;
    
    const drawMockQR = () => {
      // Draw border box
      ctx.strokeStyle = "#e5e7eb";
      ctx.lineWidth = 1;
      ctx.strokeRect(width / 2 - 45, footerY - 50, 90, 90);
      
      // Draw grid
      ctx.fillStyle = "#111827";
      for (let r = 0; r < 15; r++) {
        for (let c = 0; c < 15; c++) {
          // Draw standard QR-like anchor boxes in corners
          const isAnchor = 
            (r < 4 && c < 4) || // Top-Left
            (r < 4 && c > 10) || // Top-Right
            (r > 10 && c < 4);   // Bottom-Left
          
          if (isAnchor) {
            // Anchor boxes (outer ring + inner dot)
            const edge = (r === 0 || r === 3 || c === 0 || c === 3 || r === 14 || r === 11 || c === 14 || c === 11) && 
                         !(r === 1 && c === 1) && !(r === 2 && c === 2) && !(r === 1 && c === 13) && !(r === 2 && c === 12);
            if (edge || (r === 1.5 && c === 1.5) || (r === 12 && c === 1.5) || (r === 1.5 && c === 12)) {
              ctx.fillRect(width / 2 - 42 + c * 5.6, footerY - 47 + r * 5.6, 5.6, 5.6);
            }
          } else if ((r + c) % 2 === 0 || (r * c) % 3 === 0) {
            // Random pattern
            ctx.fillRect(width / 2 - 42 + c * 5.6, footerY - 47 + r * 5.6, 5.6, 5.6);
          }
        }
      }
      resolve(canvas.toDataURL("image/png"));
    };

    qrImg.onload = () => {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(width / 2 - 47, footerY - 52, 94, 94);
      ctx.drawImage(qrImg, width / 2 - 45, footerY - 50, 90, 90);
      resolve(canvas.toDataURL("image/png"));
    };

    qrImg.onerror = () => {
      drawMockQR();
    };
  });
}
